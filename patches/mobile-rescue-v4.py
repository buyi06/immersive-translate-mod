#!/usr/bin/env python3
"""IMT-MOD mobile rescue v4 - correct custom AI instance injector.

Fixes discovered from v3 diagnostic dump:
  * UI saved only meta (name/group/type/extends) into fullLocalUserConfig.translationServices['custom-ai-XXXX'],
    losing apiUrl/apiKey/model. IMT then threw 'Cannot read properties of undefined (reading assistantId)'
    because translationService was set to 'custom-ai' (the template), not the instance ID.
  * Field name must be 'apiUrl' not 'url'.
  * Instance needs assistantId:'common' to avoid null-deref.

Replaces opt v3 block with opt v4. background.js / content_guard.js unchanged.
"""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG_OPT_V3 = b'/* IMT-MOD MOBILE RESCUE opt v3 */'
TAG_OPT_V4 = b'/* IMT-MOD MOBILE RESCUE opt v4 */'

OPT_V4 = br"""/* IMT-MOD MOBILE RESCUE opt v4 */
(function(){
  if (typeof window==='undefined') return;
  if (window.__IMT_MOD_MOBILE_RESCUE_OPT_V4__) return;
  window.__IMT_MOD_MOBILE_RESCUE_OPT_V4__=true;
  function mkBtn(label,cb,style){ var b=document.createElement('button'); b.textContent=label; b.style.cssText=(style||'padding:10px 14px;background:#0b6;color:#fff;border:0;border-radius:4px;font:13px sans-serif;cursor:pointer;margin:4px 4px 0 0'); b.onclick=cb; return b; }
  function forceCSS(){ try{ if(document.getElementById('imt-mod-v3-css')) return; var s=document.createElement('style'); s.id='imt-mod-v3-css'; s.textContent=[
    'a[href*="imtintl.com"],img[src*="imtintl.com"],iframe[src*="imtintl.com"],[data-src*="imtintl.com"]{display:none!important}',
    'a[href*="immersivetranslate.com"],iframe[src*="immersivetranslate.com"],img[src*="immersivetranslate.com"]{display:none!important}',
    '[class*="invite" i],[class*="referral" i],[class*="reward" i],[class*="trial" i],[class*="coupon" i],[class*="discount" i]{display:none!important}',
    '[class*="promo" i],[class*="banner" i],[class*="announcement" i],[class*="share-card" i]{display:none!important}',
    '[class*="need-pro" i],[class*="pro-only" i],[class*="max-only" i],[class*="lock" i]{display:none!important}',
    '[class*="download-app" i],[class*="app-store" i],[class*="google-play" i],[class*="mobile-promo" i]{display:none!important}',
    '[class*="upgrade" i],[class*="subscribe" i],[class*="vip" i],[class*="premium" i]{display:none!important}'
  ].join('\n'); (document.head||document.documentElement).appendChild(s); }catch(_){} }
  var n=0; var css=setInterval(function(){ forceCSS(); if(++n>=15) clearInterval(css); },1000);
  var errLog=[];
  try{ var _f=window.fetch; window.fetch=function(){ var t0=Date.now(); var u=arguments[0]; if(u&&u.url) u=u.url; var s=String(u).slice(0,200); return _f.apply(this,arguments).then(function(r){ if(!r.ok){ errLog.push({t:Date.now(),s:r.status,u:s,ms:Date.now()-t0}); if(errLog.length>40) errLog.shift(); } return r; }).catch(function(e){ errLog.push({t:Date.now(),s:'THROW',u:s,err:((e&&e.message)||String(e)).slice(0,200),ms:Date.now()-t0}); if(errLog.length>40) errLog.shift(); throw e; }); }; }catch(_){}
  function collect(){ return new Promise(function(resolve){ try{ chrome.runtime.sendMessage({type:'imt-mod-collect'},function(resp){ try{var le=chrome.runtime.lastError; if(le) resolve({ok:false,err:le.message||'lastError'}); else resolve(resp||{ok:false,err:'no resp'}); }catch(_){ resolve({ok:false,err:'?'}); } }); }catch(e){ resolve({ok:false,err:(e&&e.message)||String(e)}); } }); }
  function copyText(text,btn,okLabel,origLabel){ function ok(){ btn.textContent=okLabel; setTimeout(function(){btn.textContent=origLabel;},2500); } try{ navigator.clipboard.writeText(text).then(ok,fb); }catch(_){ fb(); } function fb(){ try{ var ta=document.createElement('textarea'); ta.value=text; ta.style.cssText='position:fixed;left:-9999px;top:-9999px'; document.body.appendChild(ta); ta.focus(); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); ok(); }catch(e){ btn.textContent='\u5931\u8D25'; } } }

  function fixOrAddCustomAI(){
    chrome.storage.local.get(['fullLocalUserConfig','translationService'], function(data){
      try{
        var cfg=(data&&data.fullLocalUserConfig)||{};
        var svcs=cfg.translationServices||{};
        var existingId=null, existing={};
        for (var k in svcs){ if (svcs[k] && svcs[k].type==='custom-ai' && /^custom-ai-/.test(k)){ existingId=k; existing=svcs[k]; break; } }
        var newInstance = !existingId;
        var id = existingId || ('custom-ai-' + Math.random().toString(36).slice(2,10));
        var apiUrl = prompt('API URL (e.g. https://api.deepseek.com/chat/completions)\n\u5F53\u524D\u503C\uFF1A'+(existing.apiUrl||'(\u7A7A)'), existing.apiUrl||'');
        if (apiUrl===null||apiUrl==='') { alert('\u5DF2\u53D6\u6D88'); return; }
        var apiKey = prompt('API Key\n\u5F53\u524D\u503C\uFF1A'+(existing.apiKey?'(\u5DF2\u8BBE\u7F6E '+existing.apiKey.slice(0,6)+'...)':'(\u7A7A)'), existing.apiKey||'');
        if (apiKey===null||apiKey==='') { alert('\u5DF2\u53D6\u6D88'); return; }
        var model = prompt('Model (e.g. deepseek-chat, gpt-4o-mini)', existing.model||'deepseek-chat');
        if (model===null||model==='') { alert('\u5DF2\u53D6\u6D88'); return; }
        var name = prompt('\u5C55\u793A\u540D', existing.name||'MyCustomAI');
        if (name===null||name==='') name = existing.name||'MyCustomAI';
        svcs[id] = {
          extends: 'custom-ai',
          group: 'custom',
          type: 'custom-ai',
          name: name,
          apiUrl: apiUrl,
          apiKey: apiKey,
          model: model,
          assistantId: 'common',
          enabled: true,
          maxTextLengthPerRequest: 1000,
          maxTextGroupLengthPerRequest: 4
        };
        cfg.translationServices = svcs;
        cfg.updatedAt = new Date().toISOString();
        cfg.localUpdatedAt = cfg.updatedAt;
        cfg.modifiedBySystem = true;
        var sets = { fullLocalUserConfig: cfg, translationService: id };
        chrome.storage.local.set(sets, function(){
          try{var le=chrome.runtime.lastError; if(le) alert('\u5199\u5165\u5931\u8D25: '+le.message); else alert((newInstance?'\u65B0\u5EFA':'\u4FEE\u590D')+' \u6210\u529F\uFF01\ninstance = '+id+'\napiUrl = '+apiUrl.slice(0,50)+'\nmodel = '+model+'\n\n\u8BF7\u5237\u65B0 Options \u9875\u5E76\u8BD5\u7FFB\u8BD1');}catch(_){}
        });
      }catch(e){ alert('\u51FA\u9519: '+((e&&e.message)||e)); }
    });
  }

  function listCustomAIInstances(){
    chrome.storage.local.get(['fullLocalUserConfig','translationService'], function(data){
      var cfg=(data&&data.fullLocalUserConfig)||{};
      var svcs=cfg.translationServices||{};
      var list=[];
      for (var k in svcs){ var v=svcs[k]||{}; list.push({id:k, type:v.type, name:v.name, extends_:v['extends'], apiUrl:v.apiUrl?v.apiUrl.slice(0,60):'(\u7A7A)', apiKey:v.apiKey?(v.apiKey.slice(0,6)+'...('+v.apiKey.length+')'):'(\u7A7A)', model:v.model||'(\u7A7A)', assistantId:v.assistantId||'(\u7A7A)', enabled:v.enabled}); }
      var report = { current_translationService: data.translationService||'(\u672A\u8BBE\u7F6E)', instances_count: list.length, instances: list };
      var text = JSON.stringify(report, null, 2);
      alert(text.slice(0, 2000));
      try{ navigator.clipboard.writeText(text); }catch(_){}
    });
  }

  function mount(){ try{ if(!document.body){ setTimeout(mount,500); return; } if(document.getElementById('imt-mod-banner')) return;
    var box=document.createElement('div'); box.id='imt-mod-banner'; box.style.cssText='position:fixed;left:0;right:0;top:0;z-index:2147483647;background:#093;color:#fff;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;padding:10px;max-height:70vh;overflow:auto;white-space:pre-wrap;word-break:break-all;box-shadow:0 2px 8px rgba(0,0,0,.35)';
    var title=document.createElement('div'); title.textContent='=== IMT-MOD \u624B\u673A\u8C03\u8BD5 v4 ==='; title.style.cssText='font-weight:bold;margin-bottom:6px'; box.appendChild(title);
    var info=document.createElement('pre'); info.id='imt-mod-banner-info'; info.style.cssText='margin:0 0 6px 0;color:#dfd;white-space:pre-wrap;word-break:break-all'; box.appendChild(info);
    var row=document.createElement('div'); row.style.cssText='display:flex;flex-wrap:wrap;gap:4px;margin-top:6px'; box.appendChild(row);

    row.appendChild(mkBtn('\U0001F527 \u4FEE\u590D/\u6DFB\u52A0 AI (\u63A8\u8350)', fixOrAddCustomAI, 'padding:14px 18px;background:#f60;color:#fff;border:0;border-radius:4px;font:bold 14px sans-serif;cursor:pointer;margin:4px 4px 0 0'));
    row.appendChild(mkBtn('\U0001F4CB \u67E5\u770B AI \u5B9E\u4F8B', listCustomAIInstances));
    var dumpBtn = mkBtn('\U0001F4CB \u4E00\u952E\u5168\u91CF\u8C03\u8BD5\u590D\u5236', function(){ var b=this; b.textContent='\u6536\u96C6\u4E2D...'; collect().then(function(resp){ var report={ v:'imt-mod-opt-dump-v4', ts:new Date().toISOString(), page_url:location.href, ua:navigator.userAgent, opt_fetch_errors:errLog.slice(-40), sw_response:resp }; var text=''; try{ text=JSON.stringify(report,null,2); }catch(e){ text='JSON fail: '+((e&&e.message)||e); } info.textContent=text.slice(0,4000)+(text.length>4000?('\n...['+text.length+' chars total, \u5168\u6587\u5DF2\u590D\u5236]'):''); copyText(text,b,'\u2713 \u5DF2\u590D\u5236','\U0001F4CB \u4E00\u952E\u5168\u91CF\u8C03\u8BD5\u590D\u5236'); }); }, 'padding:10px 14px;background:#06b;color:#fff;border:0;border-radius:4px;font:13px sans-serif;cursor:pointer;margin:4px 4px 0 0');
    row.appendChild(dumpBtn);
    row.appendChild(mkBtn('\u2715 \u9690\u85CF', function(){ box.style.display='none'; }));

    document.body.appendChild(box);
    function refresh(){ try{ var parts=[];
      chrome.storage.local.get(['fullLocalUserConfig','translationService'], function(data){
        var cfg=(data&&data.fullLocalUserConfig)||{};
        var svcs=cfg.translationServices||{};
        var customAiInstances=[];
        for (var k in svcs){ if(svcs[k]&&svcs[k].type==='custom-ai') customAiInstances.push({id:k, complete:!!(svcs[k].apiUrl&&svcs[k].apiKey&&svcs[k].model)}); }
        parts.push('V3_HARDEN: '+!!(self.__IMT_MOD_V3_HARDEN__||window.__IMT_MOD_V3_HARDEN__));
        parts.push('CSS inject: '+(document.getElementById('imt-mod-v3-css')?'YES':'NO'));
        try{ var mf=chrome.runtime.getManifest(); parts.push('Ext: '+mf.name+' v'+mf.version); }catch(_){}
        parts.push('translationService: '+(data.translationService||'(\u672A\u8BBE\u7F6E)'));
        parts.push('Custom AI \u5B9E\u4F8B: '+customAiInstances.length+(customAiInstances.length?(' ['+customAiInstances.map(function(x){return x.id+(x.complete?'\u2713':'\u2717\u6B20\u5B57\u6BB5');}).join(', ')+']'):''));
        parts.push('Fetch errors: '+errLog.length);
        info.textContent=parts.join('\n');
      });
    }catch(_){} }
    refresh(); setInterval(refresh,3000);
  }catch(_){} }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount); else mount();
})();
"""

def replace_block(path, old_tag, new_tag, new_block):
    with open(path,'rb') as f: data=f.read()
    if new_tag in data:
        print('[skip] '+path+' already has new tag'); return
    if old_tag not in data:
        print('[ERR] '+path+' missing old tag '+old_tag.decode()); sys.exit(2)
    start=data.index(old_tag)
    tail=data[start:]
    idx=tail.find(b'})();\n')
    if idx<0:
        print('[ERR] '+path+' no }();\\n after tag'); sys.exit(3)
    end=start+idx+len(b'})();\n')
    shutil.copy2(path, path+'.bak-mobile-rescue-v4')
    new=data[:start]+new_block+b'\n'+data[end:]
    with open(path,'wb') as f: f.write(new)
    print('[ok] '+path+': '+str(len(data))+' -> '+str(len(new))+' B ('+('%+d'%(len(new)-len(data)))+')')

def main():
    os.chdir(ROOT)
    replace_block('options.js', TAG_OPT_V3, TAG_OPT_V4, OPT_V4)
    print('done')

if __name__=='__main__': main()
