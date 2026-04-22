#!/usr/bin/env python3
"""
IMT-MOD patch: inject patches/static-assets-extra.css into the existing
`imt-mod-v3-css` <style> block in every bundle that carries V3 harden.

Rationale
---------
Turn 25's CSS pass hides first-party UI elements, but user reports that
several static assets (banners, illustrations, marketing images) are still
visible. static-assets-extra.css extends the blacklist. Because the CSS is
injected from JS (not loaded as a separate file), we must splice it into the
existing in-JS CSS literal.

What it does (idempotent, per file)
  - Locates the CSS literal inside the V3 harden IIFE. Pattern:
      var CSS = `...existing rules...`;
    (or equivalent with quoted string literal).
  - If the marker `/* IMT-MOD static-assets extra */` is NOT already present
    inside that literal, appends the content of static-assets-extra.css to
    the end of the literal (before the closing backtick/quote).
  - Writes a .bak-extra-css backup.

If the CSS literal shape differs between bundles (single-quoted vs backtick,
escaping), the script prints what it saw and skips the file rather than
corrupting it.

Usage
  python3 patches/inject-extra-css.py          # dry-run
  python3 patches/inject-extra-css.py --apply  # write changes
"""
import os, re, sys

TARGETS = ["background.js", "options.js", "content_main.js", "popup.js", "side-panel.js"]
MARKER = b"/* IMT-MOD static-assets extra */"

# The V3 harden CSS injection stores the rules in a variable then createElement('style').
# We locate the literal between backticks that follows `var CSS = \`` in the V3 harden IIFE.
# If the bundle uses a different form, the regex yields zero matches and we skip safely.
CSS_LIT_RE = re.compile(rb"(var CSS = `)([^`]*?)(`\s*;)", re.DOTALL)


def load_extra_css():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "static-assets-extra.css")
    with open(path, "rb") as f:
        return f.read()


def patch_file(path, extra, apply):
    with open(path, "rb") as f: b = f.read()
    if MARKER in b:
        return True, ["already patched (marker present) — skipped"]

    matches = list(CSS_LIT_RE.finditer(b))
    if len(matches) != 1:
        return False, [f"CSS literal not matched uniquely (count={len(matches)}); skipped to avoid corruption"]

    m = matches[0]
    pre_open, body, close = m.group(1), m.group(2), m.group(3)
    # Append extra (prefix with newline + marker for idempotency check).
    new_body = body + b"\n\n" + MARKER + b"\n" + extra + b"\n"
    b2 = b[:m.start()] + pre_open + new_body + close + b[m.end():]

    if apply:
        with open(path + ".bak-extra-css", "wb") as f: f.write(b)
        with open(path, "wb") as f: f.write(b2)
        return True, [f"injected ({len(b)} -> {len(b2)} bytes, +{len(b2)-len(b)})", "WRITTEN (backup: .bak-extra-css)"]
    return True, [f"dry-run: would inject ({len(b)} -> {len(b2)} bytes, +{len(b2)-len(b)})"]


def main():
    apply = "--apply" in sys.argv
    extra = load_extra_css()
    root = os.getcwd()
    ok_all = True
    for name in TARGETS:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            print(f"{name}: NOT FOUND"); continue
        ok, rep = patch_file(path, extra, apply)
        print(f"=== {name} ===")
        for line in rep: print("  " + line)
        if not ok: ok_all = False
    print()
    print("OK" if ok_all else "DONE with skips (inspect output, may need manual splice)")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
