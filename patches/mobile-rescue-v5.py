#!/usr/bin/env python3
# mobile-rescue v5: fix button now also writes customAiAssistants entry,
# cleans up broken custom-ai-* instances (missing apiUrl/apiKey), and
# auto-reloads the Options page after success so the IMT UI picks up changes.
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT = os.path.join(ROOT, 'options.js')

OLD = (
        "        var sets = { fullLocalUserConfig: cfg, translationService: id };\n"
        "        chrome.storage.local.set(sets, function(){\n"
        "          try{var le=chrome.runtime.lastError; if(le) alert('\\u5199\\u5165\\u5931\\u8D25: '+le.message); else alert((newInstance?'\\u65B0\\u5EFA':'\\u4FEE\\u590D')+' \\u6210\\u529F\\uFF01\\ninstance = '+id+'\\napiUrl = '+apiUrl.slice(0,50)+'\\nmodel = '+model+'\\n\\n\\u8BF7\\u5237\\u65B0 Options \\u9875\\u5E76\\u8BD5\\u7FFB\\u8BD1');}catch(_){}\n"
        "        });\n"
)

NEW = (
        "        // v5: clean up broken custom-ai-* entries (missing apiUrl/apiKey)\n"
        "        var removed=[];\n"
        "        for (var bk in svcs){ if (bk!==id && /^custom-ai-/.test(bk)){ var bv=svcs[bk]||{}; if(!(bv.apiUrl&&bv.apiKey&&bv.model)){ delete svcs[bk]; removed.push(bk); } } }\n"
        "        cfg.translationServices = svcs;\n"
        "        // v5: also maintain customAiAssistants so IMT UI #ai tab shows an entry and translation path sees it\n"
        "        var assistants = Array.isArray(cfg.customAiAssistants) ? cfg.customAiAssistants.slice() : [];\n"
        "        var assistId = 'custom-' + id.replace(/^custom-ai-/,'');\n"
        "        var existingAssistIdx = -1;\n"
        "        for (var ai=0; ai<assistants.length; ai++){ if(assistants[ai] && (assistants[ai].id===assistId || assistants[ai].id===id)){ existingAssistIdx=ai; break; } }\n"
        "        var assistEntry = {\n"
        "          id: assistId,\n"
        "          name: name,\n"
        "          avatar: '',\n"
        "          priority: 0,\n"
        "          custom: true,\n"
        "          description: '',\n"
        "          version: '1.0.0',\n"
        "          extensionVersion: '1.4.10',\n"
        "          details: '',\n"
        "          author: '',\n"
        "          homepage: '',\n"
        "          props: [],\n"
        "          matches: [],\n"
        "          env: {},\n"
        "          systemPrompt: '',\n"
        "          prompt: '',\n"
        "          multipleSystemPrompt: '',\n"
        "          multiplePrompt: '',\n"
        "          subtitlePrompt: '',\n"
        "          langOverrides: [],\n"
        "          heat: 0,\n"
        "          i18n: {},\n"
        "          maxTextGroupLengthPerRequest: 4,\n"
        "          maxTextLengthPerRequest: 1200,\n"
        "          translationServiceId: id\n"
        "        };\n"
        "        if (existingAssistIdx>=0) assistants[existingAssistIdx]=assistEntry; else assistants.push(assistEntry);\n"
        "        cfg.customAiAssistants = assistants;\n"
        "        var sets = { fullLocalUserConfig: cfg, translationService: id };\n"
        "        chrome.storage.local.set(sets, function(){\n"
        "          try{var le=chrome.runtime.lastError;\n"
        "            if(le){ alert('\\u5199\\u5165\\u5931\\u8D25: '+le.message); return; }\n"
        "            var msg=(newInstance?'\\u65B0\\u5EFA':'\\u4FEE\\u590D')+' \\u6210\\u529F\\uFF01\\n'\n"
        "              +'service = '+id+'\\n'\n"
        "              +'assistant = '+assistId+'\\n'\n"
        "              +'apiUrl = '+apiUrl.slice(0,50)+'\\n'\n"
        "              +'model = '+model+'\\n'\n"
        "              +(removed.length?('\\n\\u5DF2\\u6E05\\u7406\\u7834\\u635F\\u6761\\u76EE: '+removed.join(', ')+'\\n'):'')\n"
        "              +'\\n\\u9875\\u9762\\u5C06\\u5728 1.5s \\u540E\\u81EA\\u52A8\\u5237\\u65B0\\u4EE5\\u52A0\\u8F7D\\u65B0\\u914D\\u7F6E';\n"
        "            alert(msg);\n"
        "            setTimeout(function(){ try{ location.reload(); }catch(_){} }, 1500);\n"
        "          }catch(_){}\n"
        "        });\n"
)

def main():
    with open(OPT, 'rb') as f:
        data = f.read()
    old_b = OLD.encode('utf-8')
    new_b = NEW.encode('utf-8')
    if old_b not in data:
        # idempotent check
        if b'v5: clean up broken custom-ai-* entries' in data:
            print('[skip] v5 already applied')
            return
        print('[err] v4 success-callback block not found in options.js', file=sys.stderr)
        sys.exit(1)
    bak = OPT + '.bak-mobile-rescue-v5'
    if not os.path.exists(bak):
        shutil.copyfile(OPT, bak)
    old_size = len(data)
    data = data.replace(old_b, new_b, 1)
    # bump visible banner tag v4 -> v5
    data = data.replace(b'\\u624B\\u673A\\u8C03\\u8BD5 v4', b'\\u624B\\u673A\\u8C03\\u8BD5 v5', 1)
    data = data.replace(b'imt-mod-opt-dump-v4', b'imt-mod-opt-dump-v5', 1)
    with open(OPT, 'wb') as f:
        f.write(data)
    print(f'[ok] options.js: {old_size} -> {len(data)} B ({len(data)-old_size:+d})')
    print('done')

if __name__=='__main__':
    main()
