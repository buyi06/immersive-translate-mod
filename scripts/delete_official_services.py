#!/usr/bin/env python3
"""Delete first-party (IMT-hosted) paid/free translator services from default_config*.json.
Keeps BYOK services (user's own API keys, including `zhipu`, `openai`, `gemini`, etc.).
"""
import json

# Services whose transport/auth is first-party (routed through immersivetranslate gateway)
DELETE = {
    'dpro',
    'free-model',
    'babel-lite-free', 'babel-lite-free.add_v.[1.23.9]',
    'zhipu-pro', 'zhipu-pro.add_v.[1.15.3]',
    'zhipu-air-pro', 'zhipu-air-pro.add_v.[1.20.12]',
    'zhipu-base',
    'zhipu-free',
}

for path in ['patched/default_config.json', 'patched/default_config.content.json']:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    ts = data.get('translationServices')
    if not isinstance(ts, dict):
        continue
    removed = []
    for k in list(DELETE):
        if k in ts:
            del ts[k]
            removed.append(k)
    # Also purge any service whose default-selected value is in DELETE
    if data.get('translationService') in DELETE:
        data['translationService'] = 'bing'
    # Keep BYOK `ai` template but force invisible as standalone picker
    ai = ts.get('ai')
    if isinstance(ai, dict):
        ai['visible'] = False
        ai['hidden'] = True
        ai['defaultVisible'] = False
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',',':'))
    print(f'{path}: removed {len(removed)} services -> {removed}')

# Also scrub translator-related options in default_config.json itself
with open('patched/default_config.json','r',encoding='utf-8') as f:
    d = json.load(f)
# Force default picks away from IMT services if anything still points there
if d.get('translationService') in DELETE or d.get('translationService') is None:
    d['translationService'] = 'bing'
for k in ('clientImageTranslationService','inputTranslationService'):
    v = d.get(k)
    if v in DELETE:
        d[k] = 'inherit'
with open('patched/default_config.json','w',encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, separators=(',',':'))
print('defaults normalized')
