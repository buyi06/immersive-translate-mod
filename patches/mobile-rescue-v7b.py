#!/usr/bin/env python3
# v7b: add a TOP-LEVEL auto-migration pass that runs on options page LOAD,
#      not only inside the 🔧 button handler. This way, existing users with
#      broken v5-written entries self-heal the first time they open Options.
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT  = os.path.join(ROOT, 'options.js')

ANCHOR = b'  if (window.__IMT_MOD_MOBILE_RESCUE_OPT_V4__) return;\n  window.__IMT_MOD_MOBILE_RESCUE_OPT_V4__=true;\n'
# inject migration right after the guard
INJECT = (
    b'  // v7b: one-shot auto-migration - copy apiKey -> APIKEY/authKey on every custom-ai-* entry\n'
    b'  try{ chrome.storage.local.get(["fullLocalUserConfig"], function(d){ try{\n'
    b'    var cfg = d && d.fullLocalUserConfig; if(!cfg) return;\n'
    b'    var svcs = cfg.translationServices || {}; var changed=0; var ids=[];\n'
    b'    for (var k in svcs){ var v = svcs[k]; if (!v || typeof v !== "object") continue;\n'
    b'      var isCustomAi = v.type === "custom-ai" || /^custom-ai/.test(k);\n'
    b'      if (!isCustomAi) continue;\n'
    b'      if (v.apiKey && !v.APIKEY){ v.APIKEY = v.apiKey; changed++; ids.push(k); }\n'
    b'      if (v.apiKey && !v.authKey){ v.authKey = v.apiKey; changed++; }\n'
    b'      if (v.APIKEY && !v.apiKey){ v.apiKey = v.APIKEY; changed++; ids.push(k); }\n'
    b'    }\n'
    b'    if (changed){ cfg.translationServices = svcs; chrome.storage.local.set({fullLocalUserConfig: cfg}, function(){\n'
    b'      try{ console.log("[imt-mod v7b] auto-migrated custom-ai APIKEY for", ids); }catch(_){}\n'
    b'    }); }\n'
    b'  }catch(e){ try{console.error("[imt-mod v7b] migration err", e);}catch(_){} } }); }catch(_){}\n'
)

def main():
    with open(OPT, 'rb') as f: data = f.read()
    if b'v7b: one-shot auto-migration' in data:
        print('[skip] v7b already applied'); return
    if ANCHOR not in data:
        print('[err] v7b anchor not found', file=sys.stderr); sys.exit(1)
    bak = OPT + '.bak-mobile-rescue-v7b'
    if not os.path.exists(bak): shutil.copyfile(OPT, bak)
    old_size = len(data)
    data = data.replace(ANCHOR, ANCHOR + INJECT, 1)
    with open(OPT, 'wb') as f: f.write(data)
    print(f'[ok] options.js: {old_size} -> {len(data)} B ({len(data)-old_size:+d})')

if __name__=='__main__': main()
