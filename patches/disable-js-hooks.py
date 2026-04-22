#!/usr/bin/env python3
"""
IMT-MOD patch: neutralize JS-level Request/fetch/XHR hooks across all bundles.

Rationale
---------
The body-builder (handleBodyHeaders({model, messages, ...s})) is byte-identical
between original and MOD, yet custom-AI verify fails with 400 "request must
include 'model' and 'messages'" / 500 "field messages is required". Therefore
the regression comes from a side channel: the JS Request-constructor wrap
(__IMT_MOD_V3_HARDEN__) and the fetch / XHR.send wraps (__IMT_MOD_CORE_V2__)
introduced in earlier turns. These JS hooks are functionally redundant with
rules_imt_block.json (DNR blocks the same hosts at the network layer), so the
safest fix is to turn them into pure pass-throughs and rely on DNR for
kill-switch behaviour. PRO_USER forging + UI hides + sendMessage wrapper stay.

What it does (idempotent, per file)
  1. try { G.Request = WrappedRequest; } catch(_){}
       -> try { /* IMT-MOD: Request wrap disabled (DNR backstop) */ } catch(_){}
  2. G.fetch = function(input, init){ ...full body... };
       -> G.fetch = function(input, init){ return origFetch(input, init); };
  3. XHR.prototype.open = function(method, url){ ...full body... };
       -> XHR.prototype.open = function(){ return origOpen.apply(this, arguments); };
  4. XHR.prototype.send = function(){ ...full body... };
       -> XHR.prototype.send = function(){ return origSend.apply(this, arguments); };

Each replacement asserts exactly ONE match before writing. A .bak-disable-hooks
backup is written beside each modified file.

Usage
  cd /root/projects/linux-audit/immersive-translate-mod-repo
  python3 patches/disable-js-hooks.py         # dry-run: prints plan
  python3 patches/disable-js-hooks.py --apply # writes changes

After applying: rebuild zip, reload unpacked, retry custom-AI verify.
If verify POSTs to nodc.pp.ua now carry model + messages in the body,
this was the regression source. If not, roll back with .bak-disable-hooks.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(os.path.dirname(__file__))) if __file__ != "<stdin>" else os.getcwd()
TARGETS = ["background.js", "options.js", "content_main.js", "offscreen.js", "popup.js", "side-panel.js"]

REQ_OLD = b"try { G.Request = WrappedRequest; } catch(_){}"
REQ_NEW = b"try { /* IMT-MOD: Request wrap disabled (DNR backstop) */ } catch(_){}"

# Regex bodies use DOTALL. Anchored on the opening signature and a specific
# closing return-statement so we never over-consume.
FETCH_RE = re.compile(
    rb"G\.fetch = function\(input, init\)\{\s*try \{.*?return origFetch\(input, init\);\s*\};",
    re.DOTALL,
)
FETCH_NEW = b"G.fetch = function(input, init){ return origFetch(input, init); };"

XHR_OPEN_RE = re.compile(
    rb"XHR\.prototype\.open = function\(method, url\)\{.*?return origOpen\.apply\(this, arguments\);\s*\};",
    re.DOTALL,
)
XHR_OPEN_NEW = b"XHR.prototype.open = function(){ return origOpen.apply(this, arguments); };"

# XHR.send wrap ends with `return origSend.apply(this, arguments);\n    };` in current bundles.
XHR_SEND_RE = re.compile(
    rb"XHR\.prototype\.send = function\(\)\{.*?return origSend\.apply\(this, arguments\);\s*\};",
    re.DOTALL,
)
XHR_SEND_NEW = b"XHR.prototype.send = function(){ return origSend.apply(this, arguments); };"

def patch_file(path, apply):
    with open(path, "rb") as f:
        b = f.read()
    orig_len = len(b)
    report = []

    # 1. Request wrap assignment (only in files that have V3 harden)
    n_req = b.count(REQ_OLD)
    if n_req == 1:
        b = b.replace(REQ_OLD, REQ_NEW)
        report.append("request_wrap: DISABLED")
    elif n_req == 0:
        report.append("request_wrap: (absent, skipped)")
    else:
        report.append(f"request_wrap: ABORT count={n_req}")
        return False, report

    # 2. fetch wrap
    mf = FETCH_RE.findall(b)
    if len(mf) == 1:
        b = FETCH_RE.sub(FETCH_NEW, b)
        report.append("fetch_hook:   PASSTHROUGH")
    else:
        report.append(f"fetch_hook:   ABORT count={len(mf)}")
        return False, report

    # 3. XHR.open wrap
    mo = XHR_OPEN_RE.findall(b)
    if len(mo) == 1:
        b = XHR_OPEN_RE.sub(XHR_OPEN_NEW, b)
        report.append("xhr_open:     PASSTHROUGH")
    else:
        report.append(f"xhr_open:     ABORT count={len(mo)}")
        return False, report

    # 4. XHR.send wrap
    ms = XHR_SEND_RE.findall(b)
    if len(ms) == 1:
        b = XHR_SEND_RE.sub(XHR_SEND_NEW, b)
        report.append("xhr_send:     PASSTHROUGH")
    else:
        report.append(f"xhr_send:     ABORT count={len(ms)}")
        return False, report

    report.append(f"size: {orig_len} -> {len(b)} ({len(b)-orig_len:+d})")

    if apply:
        with open(path + ".bak-disable-hooks", "wb") as f:
            f.write(open(path, "rb").read())
        with open(path, "wb") as f:
            f.write(b)
        report.append("WRITTEN (backup: .bak-disable-hooks)")
    else:
        report.append("dry-run (pass --apply to write)")
    return True, report


def main():
    apply = "--apply" in sys.argv
    root = os.getcwd()
    ok_all = True
    for name in TARGETS:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            print(f"{name}: NOT FOUND"); continue
        ok, rep = patch_file(path, apply)
        print(f"=== {name} ===")
        for line in rep:
            print("  " + line)
        if not ok:
            ok_all = False
    print()
    print("OK" if ok_all else "FAILED (see ABORT lines above)")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
