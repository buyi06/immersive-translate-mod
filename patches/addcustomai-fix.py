#!/usr/bin/env python3
"""
IMT-MOD patch: locate and disable the "Add custom AI assistant" consent gate.

Rationale
---------
In Turn 25 we fixed a consent gate on the "Add custom translation service"
handler (function I9, pattern `x=!1,y=async ... T||w?y():(c(!0),ge(...))`) by
forcing `x=!0` so the modal opens directly without the community-agreement
popup. The "Add custom AI" button is a separate, parallel handler: it uses the
same gate shape but a different binding location, so the Turn 25 fix did not
apply, and clicking the button still "flashes" (opens the consent modal which
is now hidden by CSS, producing a no-op / crash perception).

This script is a LOCATOR, not an auto-patcher. The exact symbol names after
minification vary between bundles, so we print all candidate matches with
surrounding context for a human to pick the correct site before final patching.
Once the correct match is chosen, the script can be rerun with --apply
--pick=<1-based index> to patch that single site.

Candidate patterns (searched in options.js, popup.js, side-panel.js)
  P1  "AddCustomAiAssistant"   and variants (camelCase or i18n key)
  P2  handler pattern:  [A-Za-z_$][\w$]*=!1,[A-Za-z_$][\w$]*=async\s+function
      within 500 bytes of "aiAssistant" / "customAi" / "addAi" substring
  P3  the actual gate:  ([A-Za-z_$][\w$]*\|\|[A-Za-z_$][\w$]*)\?[A-Za-z_$][\w$]*\(\):\(
      which matches `T||w?y():(c(!0),ge(...))`

When --apply --pick=N is given, script rewrites the chosen site's `x=!1` to
`x=!0` (force consent-satisfied) and writes a .bak-addcustomai backup.

Usage
  python3 patches/addcustomai-fix.py            # locate, print candidates
  python3 patches/addcustomai-fix.py --apply --pick=2  # patch candidate #2
"""
import os, re, sys

TARGETS = ["options.js", "popup.js", "side-panel.js", "content_main.js"]

KEY_SUBSTRINGS = [
    b"customAiAssistant", b"CustomAiAssistant", b"customAi", b"CustomAi",
    b"addCustomAI", b"addCustomAi", b"AddCustomAI", b"AddCustomAi",
    b"aiAssistant", b"AI assistant",
]

# Matches  <id1>=!1,<id2>=async function
CONSENT_INIT = re.compile(rb"([A-Za-z_$][\w$]*)=!1,([A-Za-z_$][\w$]*)=async\s+function")
# Matches  T||w?y():(c(!0),ge(...))  — the gate choice.
GATE_CHOICE = re.compile(rb"([A-Za-z_$][\w$]*)\|\|([A-Za-z_$][\w$]*)\?([A-Za-z_$][\w$]*)\(\):\(([A-Za-z_$][\w$]*)\(!0\)")


def context(buf, off, before=80, after=120):
    s = max(0, off - before); e = min(len(buf), off + after)
    return buf[s:e].decode("utf-8", "replace").replace("\n", " ")


def locate(buf, name):
    """Return list of candidates: dicts with init-site offset, gate-site offset, ctx."""
    cands = []
    for m_init in CONSENT_INIT.finditer(buf):
        init_off = m_init.start()
        # Require a nearby key substring within 1KB to narrow to AI assistant handlers.
        window = buf[max(0, init_off - 1024): init_off + 1024]
        if not any(k in window for k in KEY_SUBSTRINGS):
            continue
        # Find the gate choice within 4KB after the init site.
        tail = buf[init_off: init_off + 4096]
        mg = GATE_CHOICE.search(tail)
        gate_off = (init_off + mg.start()) if mg else None
        cands.append({
            "file": name,
            "init_off": init_off,
            "init_match": m_init.group(0),
            "gate_off": gate_off,
            "gate_match": mg.group(0) if mg else None,
            "ctx": context(buf, init_off),
        })
    return cands


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    pick = None
    for a in args:
        if a.startswith("--pick="):
            pick = int(a.split("=", 1)[1])

    all_cands = []
    root = os.getcwd()
    for fn in TARGETS:
        path = os.path.join(root, fn)
        if not os.path.isfile(path): continue
        b = open(path, "rb").read()
        for c in locate(b, fn):
            c["path"] = path
            c["buf_len"] = len(b)
            all_cands.append(c)

    if not all_cands:
        print("No candidates found. Grep for other patterns or dump AI-section bytes manually.")
        sys.exit(1)

    print(f"Found {len(all_cands)} candidate(s):\n")
    for i, c in enumerate(all_cands, 1):
        print(f"[{i}] {c['file']}  init@{c['init_off']}  gate@{c['gate_off']}")
        print(f"    init: {c['init_match'].decode()}")
        if c['gate_match']:
            print(f"    gate: {c['gate_match'].decode()}")
        print(f"    ctx:  ...{c['ctx']}...")
        print()

    if not apply:
        print("Dry-run. Re-run with --apply --pick=<N> to patch a specific candidate.")
        sys.exit(0)

    if pick is None or not (1 <= pick <= len(all_cands)):
        print("--apply requires --pick=<N> where N is a 1-based index from the list above.")
        sys.exit(2)

    c = all_cands[pick - 1]
    with open(c["path"], "rb") as f: b = f.read()
    # Rewrite <id1>=!1 -> <id1>=!0 at this exact init site.
    old = c["init_match"]
    # Replace only the first occurrence at the exact offset to avoid collateral.
    assert b[c["init_off"]:c["init_off"] + len(old)] == old, "init-site bytes drifted; abort"
    new = re.sub(rb"=!1,", b"=!0,", old, count=1)
    b2 = b[:c["init_off"]] + new + b[c["init_off"] + len(old):]
    with open(c["path"] + ".bak-addcustomai", "wb") as f: f.write(b)
    with open(c["path"], "wb") as f: f.write(b2)
    print(f"Patched {c['file']} at offset {c['init_off']}  ({len(old)}->{len(new)} bytes, net {len(b2)-len(b):+d})")
    print("Backup: " + c["path"] + ".bak-addcustomai")


if __name__ == "__main__":
    main()
