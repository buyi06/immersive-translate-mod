#!/usr/bin/env python3
# mobile-rescue v7: THE real custom-ai 401 root cause.
#
# IMT's custom-ai constructor reads `a.APIKEY` (all-caps), not `apiKey`.
# See content_main.js: `if(a.APIKEY){...o=a.APIKEY?.trim();this.apiKeys=o.split(',')...}`
# Up through v5 we were only writing `apiKey` (camelCase), so `a.APIKEY` was
# undefined, `this.apiKeys` stayed unset, `getRandomKey()` returned undefined,
# no Authorization header was attached, and every request got 401.
#
# Fix, three layers:
#   1) options.js 🔧-button writes BOTH `apiKey` and `APIKEY` (and `authKey`)
#      so new/repaired entries work on every IMT service class.
#   2) options.js migrates every pre-existing custom-ai-* entry: if it has
#      `apiKey` but no `APIKEY`, copy it across. This fixes the user's two
#      already-broken instances without re-running the wizard.
#   3) content_main.js custom-ai ctor gets a runtime fallback
#      `a.APIKEY ||= a.apiKey || a.authKey` so even if some storage path
#      only has the camelCase field, the class still authenticates.
#
# Idempotent: re-running prints [skip] for each already-applied piece.
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT = os.path.join(ROOT, 'options.js')
CMAIN = os.path.join(ROOT, 'content_main.js')

# --- options.js: patch #1 + #2 ---
# Patch #1: replace the minimal cfg literal to also include APIKEY / authKey.
OPT_OLD_CFG = (
    "          apiUrl: apiUrl,\n"
    "          apiKey: apiKey,\n"
    "          model: model,\n"
)
OPT_NEW_CFG = (
    "          apiUrl: apiUrl,\n"
    "          apiKey: apiKey,\n"
    "          APIKEY: apiKey,   // v7: IMT custom-ai ctor reads uppercase\n"
    "          authKey: apiKey,  // v7: DeepL-variant ctor fallback\n"
    "          model: model,\n"
)

# Patch #2: after the v5 cleanup block, migrate surviving entries.
OPT_OLD_CLEANUP = (
    "        // v5: clean up broken custom-ai-* entries (missing apiUrl/apiKey)\n"
    "        var removed=[];\n"
    "        for (var bk in svcs){ if (bk!==id && /^custom-ai-/.test(bk)){ var bv=svcs[bk]||{}; if(!(bv.apiUrl&&bv.apiKey&&bv.model)){ delete svcs[bk]; removed.push(bk); } } }\n"
    "        cfg.translationServices = svcs;\n"
)
OPT_NEW_CLEANUP = (
    "        // v5: clean up broken custom-ai-* entries (missing apiUrl/apiKey)\n"
    "        var removed=[];\n"
    "        for (var bk in svcs){ if (bk!==id && /^custom-ai-/.test(bk)){ var bv=svcs[bk]||{}; if(!(bv.apiUrl&&bv.apiKey&&bv.model)){ delete svcs[bk]; removed.push(bk); } } }\n"
    "        // v7: migrate field name — IMT custom-ai ctor reads a.APIKEY (uppercase).\n"
    "        var migrated=[];\n"
    "        for (var mk in svcs){ var mv=svcs[mk]; if (mv && /^custom-ai/.test(mv.type||mk)) { var changed=false; if (mv.apiKey && !mv.APIKEY){ mv.APIKEY=mv.apiKey; changed=true; } if (mv.apiKey && !mv.authKey){ mv.authKey=mv.apiKey; changed=true; } if (mv.APIKEY && !mv.apiKey){ mv.apiKey=mv.APIKEY; changed=true; } if (changed) migrated.push(mk); } }\n"
    "        cfg.translationServices = svcs;\n"
)

# --- content_main.js: patch #3 ---
# Injects the fallback immediately before IMT's own `if(a.APIKEY){...}` guard
# in the custom-ai constructor. Matches on the unique literal we confirmed.
CMAIN_OLD = b"a.APIKEY){if(rd(a.APIKEY))"
CMAIN_NEW = b"a.APIKEY=a.APIKEY||a.apiKey||a.authKey,a.APIKEY){if(rd(a.APIKEY))"

def patch_file(path, pairs, marker_checks):
    with open(path, 'rb') as f:
        data = f.read()
    orig_size = len(data)
    changed_any = False
    for idx, (old, new, label) in enumerate(pairs):
        if isinstance(old, str): old = old.encode('utf-8')
        if isinstance(new, str): new = new.encode('utf-8')
        if old in data:
            data = data.replace(old, new, 1)
            print(f'[ok] {os.path.basename(path)}: applied {label}')
            changed_any = True
        elif marker_checks[idx] and marker_checks[idx] in data:
            print(f'[skip] {os.path.basename(path)}: {label} already applied')
        else:
            print(f'[err] {os.path.basename(path)}: could not locate {label}', file=sys.stderr)
            sys.exit(2)
    if changed_any:
        bak = path + '.bak-mobile-rescue-v7'
        if not os.path.exists(bak):
            # take bak from on-disk pre-edit state
            with open(bak, 'wb') as bf: bf.write(open(path,'rb').read() if not changed_any else b'')  # placeholder; see below
    return data, changed_any, orig_size

def apply(path, pairs):
    with open(path, 'rb') as f:
        data = f.read()
    orig = data
    applied = []
    for old, new, marker, label in pairs:
        if isinstance(old, str): ob = old.encode('utf-8')
        else: ob = old
        if isinstance(new, str): nb = new.encode('utf-8')
        else: nb = new
        if ob in data:
            data = data.replace(ob, nb, 1)
            applied.append(label)
            print(f'[ok] {os.path.basename(path)}: {label}')
        elif marker and marker.encode('utf-8') in data:
            print(f'[skip] {os.path.basename(path)}: {label} already applied')
        else:
            print(f'[err] {os.path.basename(path)}: cannot locate {label}', file=sys.stderr)
            sys.exit(2)
    if data != orig:
        bak = path + '.bak-mobile-rescue-v7'
        if not os.path.exists(bak):
            shutil.copyfile(path, bak)
        with open(path, 'wb') as f:
            f.write(data)
        print(f'[ok] {os.path.basename(path)}: {len(orig)} -> {len(data)} B ({len(data)-len(orig):+d})')
    else:
        print(f'[noop] {os.path.basename(path)}')

def main():
    apply(OPT, [
        (OPT_OLD_CFG, OPT_NEW_CFG,
         'APIKEY: apiKey,   // v7: IMT custom-ai ctor reads uppercase',
         'options.js: write APIKEY/authKey alongside apiKey'),
        (OPT_OLD_CLEANUP, OPT_NEW_CLEANUP,
         'v7: migrate field name',
         'options.js: migrate existing custom-ai-* entries to APIKEY'),
    ])
    apply(CMAIN, [
        (CMAIN_OLD, CMAIN_NEW,
         'a.APIKEY=a.APIKEY||a.apiKey||a.authKey',
         'content_main.js: runtime APIKEY fallback in custom-ai ctor'),
    ])
    # Bump the banner tag so the user can visually confirm the new build loaded.
    with open(OPT, 'rb') as f: d = f.read()
    # \u624B\u673A\u8C03\u8BD5 = "手机调试"
    new_d = d.replace(b'\\u624B\\u673A\\u8C03\\u8BD5 v5', b'\\u624B\\u673A\\u8C03\\u8BD5 v7', 1)
    new_d = new_d.replace(b'imt-mod-opt-dump-v5', b'imt-mod-opt-dump-v7', 1)
    if new_d != d:
        with open(OPT, 'wb') as f: f.write(new_d)
        print('[ok] options.js banner bumped v5 -> v7')
    print('done')

if __name__=='__main__':
    main()
