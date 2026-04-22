#!/usr/bin/env python3
"""Turn-10 comprehensive fix (covers all 7 user-reported issues)."""
import json, os, sys, re

TARGET = sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),'..','patched')
TARGET = os.path.abspath(TARGET)
print(f'[turn10] target={TARGET}')

# ---------- 1/6/7. Scrub default_config*.json ----------
def scrub_config(path):
    if not os.path.exists(path):
        print(f'[turn10] skip (not found): {path}'); return False
    with open(path,'r',encoding='utf-8') as f:
        cfg = json.load(f)
    ts = cfg.get('translationServices', {}) or {}
    dead = []
    for k,v in list(ts.items()):
        if not isinstance(v, dict): continue
        grp = v.get('group'); prov = v.get('provider'); typ = v.get('type')
        if grp in ('free','pro','max') or prov == 'pro' or typ in ('zhipu-pro','zhipu-base','zhipu-free','free-model','babel-lite-free','dpro'):
            dead.append(k)
    for k in dead: ts.pop(k, None)
    cfg['translationServices'] = ts

    DEAD_TOKENS = set(dead) | {'free-model','babel-lite-free','dpro','zhipu-pro','zhipu-base','zhipu-free','zhipu-air-pro'}
    def walk(node):
        if isinstance(node, dict):
            for key in list(node.keys()):
                val = node[key]
                kl = key.lower()
                if isinstance(val, list) and ('order' in kl or 'services' in kl or 'detection' in kl):
                    node[key] = [x for x in val if not (isinstance(x,str) and x in DEAD_TOKENS)]
                elif isinstance(val, str) and val in DEAD_TOKENS and key in ('translationService','service','commonService'):
                    node[key] = 'bing'
                else:
                    walk(val)
            if 'enableFreeModelMode' in node: node['enableFreeModelMode'] = False
            if 'commonService' in node and isinstance(node['commonService'], dict):
                if node['commonService'].get('service') in DEAD_TOKENS:
                    node['commonService']['service'] = 'custom-ai'
        elif isinstance(node, list):
            for it in node: walk(it)
    walk(cfg)

    cfg['alpha'] = True; cfg['beta'] = True; cfg['canary'] = True

    gr = cfg.setdefault('generalRule', {})
    sr = gr.setdefault('subtitleRule', {})
    sr['preTranslation'] = True
    sr['aiSmartSentence'] = True
    sr['ytAIAsr'] = True
    cfg.setdefault('subtitleRule', {}).update({'preTranslation': True, 'ytAIAsr': True, 'aiSmartSentence': True})

    existing = cfg.get('aiAssistants')
    if not (isinstance(existing, list) and len(existing) > 0):
        general = {'id':'general','key':'general','custom':False,'name':'\u901a\u7528\u7ffb\u8bd1','description':'\u901a\u7528\u7ffb\u8bd1\u4e13\u5bb6\uff08\u9ed8\u8ba4\uff09','priority':0,'matches':[],'systemPrompt':'You are a professional translator. Translate the given text. Output ONLY the translation.','prompt':'Translate the following to the target language:\ntext','contextPrompt':'','version':'1.0.0','hidden':False}
        paraphrase = {'id':'paraphrase','key':'paraphrase','custom':False,'name':'\u6da6\u8272','description':'\u6da6\u8272\u7ffb\u8bd1','priority':1,'matches':[],'systemPrompt':'You are a professional editor. Translate with clarity and natural flow.','prompt':'Polish and translate:\ntext','version':'1.0.0','hidden':False}
        cfg['aiAssistants'] = [general, paraphrase]
    ids = cfg.get('aiAssistantIds') or []
    for must in ('general','paraphrase'):
        if must not in ids: ids.insert(0, must)
    cfg['aiAssistantIds'] = ids
    cfg['enableAiAssistant'] = True
    cfg['defaultAiAssistant'] = 'general'

    with open(path,'w',encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, separators=(',',':'))
    print(f'[turn10] scrubbed {path}: removed {len(dead)} services, seeded {len(cfg.get("aiAssistants",[]))} assistants')
    return True

scrub_config(os.path.join(TARGET,'default_config.json'))
scrub_config(os.path.join(TARGET,'default_config.content.json'))

# ---------- options.js: About/Tutorial/BX/wL/ny ----------
op = os.path.join(TARGET,'options.js')
with open(op,'r',encoding='utf-8') as f: src = f.read()
orig_len = len(src)

about_old = ',{name:a("about"),props:{href:"#about",className:"secondary"}}'
if about_old in src:
    src = src.replace(about_old, ''); print('[turn10] options.js: removed #about footer entry')
else:
    print('[turn10] options.js: #about footer entry not found')

tut_old = ',tutorial:{label:c("sideMenu.tutorial"),Icon:vI}'
if tut_old in src:
    src = src.replace(tut_old, ''); print('[turn10] options.js: removed sidemenu tutorial')
else:
    tut_old2 = 'tutorial:{label:c("sideMenu.tutorial"),Icon:vI},'
    if tut_old2 in src:
        src = src.replace(tut_old2, ''); print('[turn10] options.js: removed sidemenu tutorial (variant)')
    else:
        print('[turn10] options.js: sidemenu tutorial not found')

sae_old = 'var sae=["text","file","video","image","tutorial"]'
if sae_old in src:
    src = src.replace(sae_old, 'var sae=["text","file","video","image"]')
    print('[turn10] options.js: removed tutorial from sae')

bx_turn9 = '.filter(s=>!(!Dn[s].allProps?.length||["zhipu-pro","qwen"].includes(s)))'
bx_restored = '.filter(s=>s==="custom-ai"||(!Dn[s].allProps?.length||["zhipu-pro","qwen"].includes(s)?!1:ny({serviceKey:s,ctx:e.ctx})))'
if bx_turn9 in src:
    src = src.replace(bx_turn9, bx_restored)
    print('[turn10] options.js: restored BX filter (ny-based)')
else:
    print('[turn10] options.js: turn-9 BX filter not found')

wl_marker = 'function wL(e){var _r=e&&e.onConfirm;if(e&&e.visible'
wl_start = src.find(wl_marker)
if wl_start >= 0:
    wl_end_pat = 'return null;}'
    wl_end = src.find(wl_end_pat, wl_start)
    if wl_end >= 0:
        old_body = src[wl_start: wl_end+len(wl_end_pat)]
        new_body = 'function wL(e){try{var _r=e&&e.onConfirm;if(e&&e.visible&&typeof _r==="function")setTimeout(function(){try{_r()}catch(_){}}, 0);}catch(_){}return null;}'
        if old_body != new_body:
            src = src.replace(old_body, new_body, 1)
            print('[turn10] options.js: wL stub -> async')
else:
    print('[turn10] options.js: wL turn-9 marker not found')

ny_probe = 'function ny(e){let{serviceKey:t,ctx:n}=e'
ny_pos = src.find(ny_probe)
if ny_pos >= 0:
    inject = 'if(t==="custom-ai")return!0;'
    first_semi = src.find(';', ny_pos)
    if first_semi>0 and inject not in src[ny_pos:ny_pos+400]:
        src = src[:first_semi+1] + inject + src[first_semi+1:]
        print('[turn10] options.js: ny() custom-ai early-return')
    else:
        print('[turn10] options.js: ny() custom-ai guard already present')
else:
    print('[turn10] options.js: ny signature not found')

if len(src) != orig_len:
    with open(op,'w',encoding='utf-8') as f: f.write(src)
    print(f'[turn10] options.js: {orig_len} -> {len(src)} bytes')
else:
    print(f'[turn10] options.js: unchanged ({orig_len} bytes)')

# ---------- Strip zhipu-pro from Dn registries ----------
def strip_zhipu_pro_dn(path):
    if not os.path.exists(path): return
    with open(path,'r',encoding='utf-8') as f: s = f.read()
    orig = s
    idx = s.find('"zhipu-pro":{')
    if idx < 0: return
    depth = 0
    i = idx + len('"zhipu-pro":')
    while i < len(s):
        ch = s[i]
        if ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: i += 1; break
        elif ch == '"':
            j = i+1
            while j < len(s):
                if s[j] == '\\': j += 2; continue
                if s[j] == '"': j += 1; break
                j += 1
            i = j; continue
        i += 1
    end = i
    if end < len(s) and s[end] == ',': end += 1
    else:
        if idx>0 and s[idx-1] == ',': idx -= 1
    s = s[:idx] + s[end:]
    if s != orig:
        with open(path,'w',encoding='utf-8') as f: f.write(s)
        print(f'[turn10] stripped zhipu-pro from Dn in {os.path.basename(path)}')

for b in ['background.js','content_main.js','offscreen.js','options.js','popup.js','side-panel.js']:
    strip_zhipu_pro_dn(os.path.join(TARGET,b))

print('[turn10] DONE')
