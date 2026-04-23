#!/usr/bin/env python3
"""IMT-MOD mobile rescue v3 - embedded DevTools for mobile.

  * Floating \U0001F50D button on every webpage (via content_guard.js)
  * Tap -> full-screen overlay with structured diagnostic dump + ONE-TAP COPY
  * Shared ring buffer in background.js (500 entries) capturing:
      - SW boot / keep-alive / onMessage / storage.onChanged / fetch hook
      - unhandledrejection + error
  * Content script pushes its own log entries (fetch errors, console.error, runtime errors) to SW
  * Options.js banner gains giant '\U0001F4CB \u4E00\u952E\u5168\u91CF\u8C03\u8BD5\u590D\u5236' button calling imt-mod-collect

Idempotent via MOBILE_RESCUE_*_V3 sentinels.
"""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG_BG_V1 = b'/* IMT-MOD MOBILE RESCUE bg v1 */'
TAG_BG_V3 = b'/* IMT-MOD MOBILE RESCUE bg v3 */'
TAG_OPT_V2 = b'/* IMT-MOD MOBILE RESCUE opt v2 */'
TAG_OPT_V3 = b'/* IMT-MOD MOBILE RESCUE opt v3 */'
TAG_CG_V3 = b'/* IMT-MOD MOBILE RESCUE cg v3 */'

BG_V3 = br"""/* IMT-MOD MOBILE RESCUE bg v3 */
(function(){
  if (typeof self === 'undefined') return;
  if (self.__IMT_MOD_MOBILE_RESCUE_BG_V3__) return;
  self.__IMT_MOD_MOBILE_RESCUE_BG_V3__ = true;
  var MAX=500, logs=[];
  function push(src,evt,ex){ try{ logs.push({t:Date.now(),src:src,evt:String(evt).slice(0,80),ex:ex}); if(logs.length>MAX) logs.splice(0,logs.length-MAX); }catch(_){} }
  self.__imt_mod_log_push = push;
  push('bg','boot',{v:3, ua:(self.navigator&&self.navigator.userAgent)||'?'});
  var SEED={hasAgreedCustomServiceConsent:true,hasAgreedCustomServiceConsent_v2:true,hasAgreedCustomServiceConsent_v3:true,hasAgreed3rdPartyConsent:true,hasAgreedPrivacyPolicy:true,isPro:true,isMax:true,isVip:true,isPremium:true,plan:'max',level:'max',membership:'max',subscription:{active:true,plan:'max',level:'max',expiresAt:9999999999000},user:{id:'local',plan:'max',isPro:true,isMax:true,isVip:true,active:true},imt_mod_ready:true,imt_mod_ready_ts:Date.now(),imt_mod_rescue_v:3};
  function seed(){ try{chrome.storage.local.set(SEED,function(){});}catch(_){} try{chrome.storage.sync&&chrome.storage.sync.set(SEED,function(){});}catch(_){} }
  try{seed();}catch(_){}
  try{chrome.runtime.onInstalled&&chrome.runtime.onInstalled.addListener(function(){push('bg','onInstalled',null);seed();});}catch(_){}
  try{chrome.runtime.onStartup&&chrome.runtime.onStartup.addListener(function(){push('bg','onStartup',null);seed();});}catch(_){}
  try{ if(chrome.alarms&&chrome.alarms.create){ chrome.alarms.create('imt-mod-keepalive',{periodInMinutes:0.35}); chrome.alarms.onAlarm.addListener(function(a){ if(a&&a.name==='imt-mod-keepalive'){ try{chrome.runtime.getPlatformInfo(function(){});}catch(_){}} });} }catch(_){}
  try{ var _f=self.fetch; self.fetch=function(){ var t0=Date.now(); var r=arguments[0]; var u=(typeof r==='string')?r:((r&&r.url)||'?'); var short=String(u).slice(0,180); return _f.apply(this,arguments).then(function(resp){ push('bg-fetch', resp.status, {u:short, ms:Date.now()-t0}); return resp; }).catch(function(e){ push('bg-fetch','THROW',{u:short, err:(e&&e.message)||String(e), ms:Date.now()-t0}); throw e; }); }; }catch(_){}
  try{ self.addEventListener('unhandledrejection',function(e){ push('bg','unhandledrejection',{msg:((e.reason&&(e.reason.message||String(e.reason)))||'?').slice(0,200)}); }); self.addEventListener('error',function(e){ push('bg','error',{msg:(e.message||'?').slice(0,200), f:(e.filename||'?')+':'+e.lineno}); }); }catch(_){}
  try{ chrome.storage.onChanged.addListener(function(changes,area){ var ks=Object.keys(changes||{}).slice(0,6); push('bg','storage.onChanged',{area:area,keys:ks}); }); }catch(_){}
  try{ chrome.runtime.onMessage.addListener(function(msg,sender,reply){
    if(!msg||typeof msg!=='object') return;
    if(msg.type==='imt-mod-ping'){ push('bg','ping',{from:(sender&&sender.url)?sender.url.slice(0,80):'?'}); try{seed();}catch(_){} try{reply({ok:true,ts:Date.now(),rescue:3,v:3,logs:logs.length});}catch(_){} return true; }
    if(msg.type==='imt-mod-log-push'){ push('cs', msg.evt||'?', msg.ex||null); try{reply({ok:true});}catch(_){} return true; }
    if(msg.type==='imt-mod-collect'){
      (async function(){
        try{
          var all=await new Promise(function(r){chrome.storage.local.get(null,r);});
          var totalKeys=Object.keys(all).length;
          var relevant={};
          for(var k in all){ var kl=k.toLowerCase(); if(kl.indexOf('custom')>=0||kl.indexOf('translation')>=0||kl.indexOf('service')>=0||kl.indexOf('ai')>=0||kl.indexOf('pro')>=0||kl.indexOf('consent')>=0||kl.indexOf('plan')>=0||kl.indexOf('user')>=0||kl.indexOf('subscr')>=0||kl.indexOf('engine')>=0||kl.indexOf('api')>=0||kl.indexOf('key')>=0||kl.indexOf('imt_mod')>=0){ var s=''; try{s=typeof all[k]==='string'?all[k]:JSON.stringify(all[k]);}catch(_){s='[unserializable]';} if(s.length>600) s=s.slice(0,600)+'...['+s.length+'B]'; relevant[k]=s; } }
          var mf=chrome.runtime.getManifest();
          var dump={ v:'imt-mod-bg-dump-v3', ts:new Date().toISOString(), ext:{id:chrome.runtime.id,name:mf.name,ver:mf.version}, storage_total_keys:totalKeys, storage_relevant:relevant, logs_count:logs.length, logs:logs.slice(-250) };
          reply({ok:true, dump:dump});
        }catch(e){ try{reply({ok:false, err:(e&&e.message)||String(e)});}catch(_){} }
      })();
      return true;
    }
  }); }catch(_){}
})();
"""

CG_V3 = br"""/* IMT-MOD MOBILE RESCUE cg v3 */
(function(){
  if (typeof window==='undefined') return;
  if (window.__IMT_MOD_MOBILE_RESCUE_CG_V3__) return;
  window.__IMT_MOD_MOBILE_RESCUE_CG_V3__=true;
  try{ if(window.top!==window) return; }catch(_){ return; }
  try{ if(!/^https?:|^file:/.test(location.href)) return; }catch(_){ return; }
  var csLogs=[];
  function log(evt,ex){ try{ csLogs.push({t:Date.now(),evt:String(evt).slice(0,80),ex:ex}); if(csLogs.length>200) csLogs.splice(0,csLogs.length-200); }catch(_){} try{ chrome.runtime.sendMessage({type:'imt-mod-log-push',evt:evt,ex:ex},function(){ try{var _=chrome.runtime.lastError;}catch(__){} }); }catch(_){} }
  log('cs-boot',{url:location.href.slice(0,120)});
  try{ var _f=window.fetch; window.fetch=function(){ var t0=Date.now(); var u=arguments[0]; if(u&&u.url) u=u.url; var s=String(u).slice(0,160); return _f.apply(this,arguments).then(function(r){ if(!r.ok) log('cs-fetch-bad',{u:s,s:r.status,ms:Date.now()-t0}); return r; }).catch(function(e){ log('cs-fetch-err',{u:s,msg:(e&&e.message)||String(e),ms:Date.now()-t0}); throw e; }); }; }catch(_){}
  try{ var _xo=XMLHttpRequest.prototype.open, _xs=XMLHttpRequest.prototype.send; XMLHttpRequest.prototype.open=function(m,u){ try{ this.__imt_u=String(u).slice(0,160); this.__imt_m=m; }catch(_){} return _xo.apply(this,arguments); }; XMLHttpRequest.prototype.send=function(){ var self_=this; var t0=Date.now(); try{ this.addEventListener('loadend',function(){ try{ if(self_.status<200||self_.status>=400) log('cs-xhr-bad',{u:self_.__imt_u,m:self_.__imt_m,s:self_.status,ms:Date.now()-t0}); }catch(_){} }); }catch(_){} return _xs.apply(this,arguments); }; }catch(_){}
  try{ var _ce=console.error; console.error=function(){ try{ var a=[].slice.call(arguments).map(function(x){ try{ return (x&&x.stack)?x.stack.slice(0,180):(typeof x==='string'?x.slice(0,180):JSON.stringify(x).slice(0,180)); }catch(_){return '?';} }).join(' '); log('cs-console.error',a.slice(0,400)); }catch(_){} return _ce.apply(console,arguments); }; }catch(_){}
  try{ window.addEventListener('error',function(e){ log('cs-error',{msg:(e.message||'?').slice(0,200),f:(e.filename||'?')+':'+e.lineno}); }); window.addEventListener('unhandledrejection',function(e){ log('cs-unhandledrejection',{msg:((e.reason&&(e.reason.message||String(e.reason)))||'?').slice(0,200)}); }); }catch(_){}
  function mkBtn(label,cb){ var b=document.createElement('button'); b.textContent=label; b.style.cssText='padding:10px 14px;background:#0b6;color:#fff;border:0;border-radius:4px;font:13px sans-serif;cursor:pointer;margin-left:6px'; b.onclick=cb; return b; }
  function mount(){ try{ if(!document.body){ setTimeout(mount,600); return; } if(document.getElementById('imt-mod-diag-btn')) return; var btn=document.createElement('button'); btn.id='imt-mod-diag-btn'; btn.textContent='\U0001F50D'; btn.style.cssText='position:fixed;right:8px;bottom:80px;z-index:2147483647;width:44px;height:44px;border-radius:50%;background:#0b6;color:#fff;border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.35);font-size:20px;cursor:pointer;line-height:40px;padding:0;text-align:center'; btn.title='IMT-MOD diagnostics'; btn.onclick=openOverlay; (document.body||document.documentElement).appendChild(btn); }catch(_){} }
  async function openOverlay(){ try{
    var ex=document.getElementById('imt-mod-diag-overlay'); if(ex){ ex.remove(); return; }
    var ov=document.createElement('div'); ov.id='imt-mod-diag-overlay'; ov.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.92);z-index:2147483647;color:#0f0;font:12px/1.45 ui-monospace,Menlo,Consolas,monospace;padding:12px 12px 70px 12px;overflow:auto;white-space:pre-wrap;word-break:break-all'; document.documentElement.appendChild(ov);
    ov.textContent='=== IMT-MOD \u8BCA\u65AD\u6536\u96C6\u4E2D... ===\n';
    var dump=null, swErr=null;
    try{ dump=await new Promise(function(res,rej){ var d=false; setTimeout(function(){ if(!d) rej(new Error('SW collect timeout 8s')); },8000); try{ chrome.runtime.sendMessage({type:'imt-mod-collect'},function(resp){ d=true; try{var le=chrome.runtime.lastError; if(le) return rej(new Error(le.message||'lastError'));}catch(_){} res(resp); }); }catch(e){ d=true; rej(e); } }); }catch(e){ swErr=(e&&e.message)||String(e); }
    var report={ v:'imt-mod-full-dump-v3', ts:new Date().toISOString(), page:{url:location.href,title:(document.title||'').slice(0,120),ua:navigator.userAgent}, ext_id:(chrome.runtime&&chrome.runtime.id)||'?', cs_logs_count:csLogs.length, cs_logs_tail:csLogs.slice(-80), sw_response:dump||null, sw_error:swErr };
    var text=''; try{ text=JSON.stringify(report,null,2); }catch(e){ text='JSON fail: '+((e&&e.message)||e); }
    ov.textContent=''; var pre=document.createElement('pre'); pre.style.cssText='white-space:pre-wrap;word-break:break-all;color:#0f0;margin:0'; pre.textContent=text; ov.appendChild(pre);
    var bar=document.createElement('div'); bar.style.cssText='position:fixed;right:8px;bottom:8px;display:flex;gap:6px;z-index:2147483647';
    bar.appendChild(mkBtn('\U0001F4CB \u590D\u5236\u5168\u90E8',function(){ var b=this; function ok(){ b.textContent='\u2713 \u5DF2\u590D\u5236'; setTimeout(function(){b.textContent='\U0001F4CB \u590D\u5236\u5168\u90E8';},2000); } try{ navigator.clipboard.writeText(text).then(ok,function(){fb();}); }catch(_){ fb(); } function fb(){ try{ var ta=document.createElement('textarea'); ta.value=text; ta.style.cssText='position:fixed;left:-9999px;top:-9999px'; document.body.appendChild(ta); ta.focus(); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); ok(); }catch(e){ b.textContent='\u590D\u5236\u5931\u8D25:'+((e&&e.message)||e).slice(0,20); } } }));
    bar.appendChild(mkBtn('\U0001F504 \u5237\u65B0',function(){ ov.remove(); openOverlay(); }));
    bar.appendChild(mkBtn('\u2715 \u5173\u95ED',function(){ ov.remove(); }));
    ov.appendChild(bar);
  }catch(e){ try{ var ov2=document.getElementById('imt-mod-diag-overlay'); if(ov2) ov2.textContent='FATAL: '+((e&&e.message)||e); }catch(__){} } }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount); else mount();
  setInterval(mount,4000);
})();
"""

OPT_V3 = br"""/* IMT-MOD MOBILE RESCUE opt v3 */
(function(){
  if (typeof window==='undefined') return;
  if (window.__IMT_MOD_MOBILE_RESCUE_OPT_V3__) return;
  window.__IMT_MOD_MOBILE_RESCUE_OPT_V3__=true;
  function mkBtn(label,cb){ var b=document.createElement('button'); b.textContent=label; b.style.cssText='padding:10px 14px;background:#0b6;color:#fff;border:0;border-radius:4px;font:13px sans-serif;cursor:pointer;margin:4px 4px 0 0'; b.onclick=cb; return b; }
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
  function mount(){ try{ if(!document.body){ setTimeout(mount,500); return; } if(document.getElementById('imt-mod-banner')) return;
    var box=document.createElement('div'); box.id='imt-mod-banner'; box.style.cssText='position:fixed;left:0;right:0;top:0;z-index:2147483647;background:#093;color:#fff;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;padding:10px;max-height:70vh;overflow:auto;white-space:pre-wrap;word-break:break-all;box-shadow:0 2px 8px rgba(0,0,0,.35)';
    var title=document.createElement('div'); title.textContent='=== IMT-MOD \u624B\u673A\u8C03\u8BD5 v3 ==='; title.style.cssText='font-weight:bold;margin-bottom:6px'; box.appendChild(title);
    var info=document.createElement('pre'); info.id='imt-mod-banner-info'; info.style.cssText='margin:0 0 6px 0;color:#dfd;white-space:pre-wrap;word-break:break-all'; box.appendChild(info);
    var row=document.createElement('div'); row.style.cssText='display:flex;flex-wrap:wrap;gap:4px;margin-top:6px'; box.appendChild(row);
    var mainBtn=mkBtn('\U0001F4CB \u4E00\u952E\u5168\u91CF\u8C03\u8BD5\u590D\u5236',function(){ var b=this; b.textContent='\u6536\u96C6\u4E2D...'; collect().then(function(resp){ var report={ v:'imt-mod-opt-dump-v3', ts:new Date().toISOString(), page_url:location.href, ua:navigator.userAgent, opt_fetch_errors:errLog.slice(-40), sw_response:resp }; var text=''; try{ text=JSON.stringify(report,null,2); }catch(e){ text='JSON fail: '+((e&&e.message)||e); } info.textContent=text.slice(0,4000)+(text.length>4000?('\n...['+text.length+' chars total, \u5168\u6587\u5DF2\u590D\u5236]'):''); copyText(text,b,'\u2713 \u5DF2\u590D\u5236','\U0001F4CB \u4E00\u952E\u5168\u91CF\u8C03\u8BD5\u590D\u5236'); }); });
    mainBtn.style.cssText='padding:14px 18px;background:#f60;color:#fff;border:0;border-radius:4px;font:bold 14px sans-serif;cursor:pointer;margin:4px 4px 0 0';
    row.appendChild(mainBtn);
    row.appendChild(mkBtn('\U0001F9E9 \u6CE8\u5165\u6D4B\u8BD5 Custom AI',function(){ var u=prompt('API URL (\u4F8B:https://api.deepseek.com/chat/completions):'); if(!u) return; var k=prompt('API Key:'); if(!k) return; var m=prompt('Model (\u4F8B:deepseek-chat):','deepseek-chat'); if(!m) return; var n=prompt('\u5C55\u793A\u540D:','MyCustomAI'); if(!n) return; var cfg={url:u,apiKey:k,model:m,name:n,enabled:true,type:'openai-custom',prompt:'Please translate into 0:\n\nagent://4fad1658-b9b1-8130-8939-00032f09c364/349d1658-b9b1-8009-9318-0092d98e3805',maxTextLengthPerRequest:1000}; var sets={}; sets['custom-ai']=cfg; sets['openai-custom']=cfg; sets['userConfig.translationServices.custom-ai']=cfg; sets['translationService']='custom-ai'; sets['translationServices.custom-ai.enabled']=true; try{ chrome.storage.local.set(sets,function(){ try{var le=chrome.runtime.lastError;}catch(_){} alert('\u5DF2\u5199\u5165 storage\uFF0C\u8BF7\u5237\u65B0 Options \u9875\u67E5\u770B\u670D\u52A1\u5217\u8868'); }); }catch(e){ alert('\u5199\u5165\u5931\u8D25:'+e.message); } }));
    row.appendChild(mkBtn('\U0001F4CB \u590D\u5236\u7B80\u6613\u8BCA\u65AD',function(){ var b=this; var dump={ V3_HARDEN: !!(window.__IMT_MOD_V3_HARDEN__||self.__IMT_MOD_V3_HARDEN__), CSS_inject: !!document.getElementById('imt-mod-v3-css'), ext: (chrome.runtime.getManifest&&chrome.runtime.getManifest().name)+' v'+chrome.runtime.getManifest().version+' id='+chrome.runtime.id, errors: errLog.slice(-10) }; var t=JSON.stringify(dump,null,2); copyText(t,b,'\u2713','\U0001F4CB \u590D\u5236\u7B80\u6613\u8BCA\u65AD'); }));
    row.appendChild(mkBtn('\u2715 \u9690\u85CF',function(){ box.style.display='none'; }));
    document.body.appendChild(box);
    function refresh(){ try{ var parts=[]; parts.push('V3_HARDEN: '+!!(self.__IMT_MOD_V3_HARDEN__||window.__IMT_MOD_V3_HARDEN__)); parts.push('CSS inject: '+(document.getElementById('imt-mod-v3-css')?'YES':'NO')); try{ var mf=chrome.runtime.getManifest(); parts.push('Ext: '+mf.name+' v'+mf.version+' id='+chrome.runtime.id); }catch(_){} parts.push('Fetch errors: '+errLog.length); info.textContent=parts.join('\n'); }catch(_){} }
    refresh(); setInterval(refresh,2000);
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
    shutil.copy2(path, path+'.bak-mobile-rescue-v3')
    new=data[:start]+new_block+b'\n'+data[end:]
    with open(path,'wb') as f: f.write(new)
    print('[ok] '+path+': '+str(len(data))+' -> '+str(len(new))+' B ('+('%+d'%(len(new)-len(data)))+')')

def prepend(path, tag, block):
    with open(path,'rb') as f: data=f.read()
    if tag in data:
        print('[skip] '+path+' already has tag'); return
    shutil.copy2(path, path+'.bak-mobile-rescue-v3')
    new=block+b'\n'+data
    with open(path,'wb') as f: f.write(new)
    print('[ok] '+path+': prepend +'+str(len(new)-len(data))+' B -> '+str(len(new)))

def main():
    os.chdir(ROOT)
    replace_block('background.js', TAG_BG_V1, TAG_BG_V3, BG_V3)
    replace_block('options.js', TAG_OPT_V2, TAG_OPT_V3, OPT_V3)
    prepend('content_guard.js', TAG_CG_V3, CG_V3)
    print('done')

if __name__=='__main__': main()
