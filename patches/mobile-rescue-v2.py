#!/usr/bin/env python3
# IMT-MOD mobile rescue v2 - replaces v1 block in options.js with richer banner.
# Adds to options.js:
#   * Force-inject V3 harden CSS (12 imtintl.com rules + Pro/VIP hides)
#   * Banner buttons:
#      - 复制诊断 / 重置解锁 / 隐藏   (unchanged from v1)
#      - 注入测试 Custom AI  (bypass UI, write directly to storage.translationServices)
#      - 列出当前翻译服务 (read storage to see what UI saved)
#      - 监听翻译错误 (hook fetch + log failures to banner)
# Idempotent: new sentinel MOBILE_RESCUE_OPT_V2

import os, shutil, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG_V1_OPT = b'/* IMT-MOD MOBILE RESCUE opt v1 */'
TAG_V2_OPT = b'/* IMT-MOD MOBILE RESCUE opt v2 */'

OPT_BLOCK_V2 = b"""/* IMT-MOD MOBILE RESCUE opt v2 */
(function(){
  if (typeof self === 'undefined') return;
  if (self.__IMT_MOD_MOBILE_RESCUE_OPT_V2__) return;
  self.__IMT_MOD_MOBILE_RESCUE_OPT_V2__ = true;
  // ---------- 0. Force-inject V3 harden CSS (does not depend on other code paths) ----------
  function forceCSS(){
    try {
      if (document.getElementById('imt-mod-v3-css')) return;
      var css = [
        '[href*="imtintl.com"],[src*="imtintl.com"],[data-src*="imtintl.com"]{display:none!important}',
        'a[href*="immersivetranslate.com"],iframe[src*="immersivetranslate.com"],img[src*="imtintl.com"]{display:none!important}',
        '[class*="invite"],[class*="referral"],[class*="reward"],[class*="trial"],[class*="coupon"],[class*="discount"]{display:none!important}',
        '[class*="promo"],[class*="banner"],[class*="announcement"],[class*="share-card"]{display:none!important}',
        '[class*="need-pro"],[class*="pro-only"],[class*="max-only"],[class*="lock"]{display:none!important}',
        '[class*="download-app"],[class*="app-store"],[class*="google-play"],[class*="mobile-promo"]{display:none!important}',
        '[class*="upgrade"],[class*="subscribe"],[class*="vip"],[class*="premium"]{display:none!important}'
      ].join('\\n');
      var s = document.createElement('style');
      s.id = 'imt-mod-v3-css';
      s.textContent = css;
      (document.head || document.documentElement).appendChild(s);
    } catch(_){}
  }
  forceCSS();
  var cssTimer = setInterval(forceCSS, 1000);
  setTimeout(function(){ clearInterval(cssTimer); }, 15000);
  // ---------- 1. Hook fetch to log translation errors ----------
  var errLog = [];
  try {
    var _f = self.fetch;
    self.fetch = function(){
      var url = arguments[0]; if (url && url.url) url = url.url;
      return _f.apply(this, arguments).then(function(resp){
        if (!resp.ok && url && String(url).length < 300) errLog.push(resp.status+' '+url);
        return resp;
      }).catch(function(e){
        if (url && String(url).length < 300) errLog.push('THROW '+e.message+' '+url);
        throw e;
      });
    };
  } catch(_){}
  // ---------- 2. Banner ----------
  function mount(){
    try {
      if (!document.body) { setTimeout(mount, 50); return; }
      if (document.getElementById('imt-mod-banner')) return;
      var st = document.createElement('style');
      st.textContent = '#imt-mod-banner{position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#0b6;color:#fff;font:12px/1.4 ui-monospace,Menlo,monospace;padding:8px 10px;box-shadow:0 2px 8px rgba(0,0,0,.25);white-space:pre-wrap;word-break:break-all;max-height:60vh;overflow:auto}#imt-mod-banner .imt-mod-fail{background:#c33;color:#fff;padding:1px 4px;border-radius:2px}#imt-mod-banner button{margin:6px 6px 0 0;background:#073;color:#fff;border:0;padding:6px 10px;border-radius:3px;font:11px monospace;cursor:pointer}#imt-mod-banner pre{background:rgba(0,0,0,.3);padding:4px;margin:4px 0;font-size:11px;white-space:pre-wrap;max-height:30vh;overflow:auto}';
      document.head.appendChild(st);
      var d = document.createElement('div');
      d.id = 'imt-mod-banner';
      d.textContent = '=== IMT-MOD \u624b\u673a\u81ea\u68c0 v2 ===';
      document.body.appendChild(d);
      try { document.body.style.paddingTop = '10px'; } catch(_){}
      run(d);
    } catch(e){ try { console.error('[imt-mod-opt-banner]', e); } catch(_){} }
  }
  function line(d, t){ d.appendChild(document.createElement('br')); d.appendChild(document.createTextNode(t)); }
  function addOutput(d, title, obj){
    var h = document.createElement('div'); h.textContent = '--- '+title+' ---'; d.appendChild(h);
    var pre = document.createElement('pre'); pre.textContent = (typeof obj === 'string') ? obj : JSON.stringify(obj, null, 2);
    d.appendChild(pre);
  }
  async function run(d){
    d.textContent = '=== IMT-MOD \u624b\u673a\u81ea\u68c0 v2 ===';
    line(d, 'V3_HARDEN: ' + !!self.__IMT_MOD_V3_HARDEN__);
    var cssEl = document.getElementById('imt-mod-v3-css');
    line(d, 'CSS inject (force): ' + (cssEl ? 'YES ('+(cssEl.textContent.match(/\\{/g)||[]).length+' rules)' : 'NO'));
    try { var mf = chrome.runtime.getManifest(); line(d, 'Ext: '+mf.name+' v'+mf.version+' id='+chrome.runtime.id); }
    catch(e){ line(d, 'manifest err: '+e.message); }
    try {
      var pong = await new Promise(function(r, rj){
        var done = false;
        setTimeout(function(){ if(!done) rj(new Error('timeout 5s')); }, 5000);
        try { chrome.runtime.sendMessage({type:'imt-mod-ping'}, function(resp){ done = true; if (chrome.runtime.lastError) { rj(new Error(chrome.runtime.lastError.message||'lastError')); } else { r(resp); } }); }
        catch(err){ done = true; rj(err); }
      });
      line(d, 'SW ping: OK '+JSON.stringify(pong));
    } catch(e){
      var span = document.createElement('span'); span.className = 'imt-mod-fail'; span.textContent = 'SW ping: FAIL - '+e.message;
      d.appendChild(document.createElement('br')); d.appendChild(span);
    }
    try {
      var s = await new Promise(function(r){ chrome.storage.local.get(['hasAgreedCustomServiceConsent','isPro','imt_mod_ready_ts','imt_mod_rescue_v'], r); });
      line(d, 'storage: '+JSON.stringify(s));
    } catch(e){ line(d, 'storage FAIL: '+e.message); }
    // Buttons area
    d.appendChild(document.createElement('br'));
    d.appendChild(document.createElement('br'));
    var mkBtn = function(label, handler){ var b = document.createElement('button'); b.textContent = label; b.onclick = handler; d.appendChild(b); return b; };
    mkBtn('\u590d\u5236\u8bca\u65ad', function(){
      try { navigator.clipboard.writeText(d.textContent); this.textContent = '\u5df2\u590d\u5236'; }
      catch(_){ var ta = document.createElement('textarea'); ta.value = d.textContent; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); this.textContent='\u5df2\u590d\u5236'; } catch(__){} document.body.removeChild(ta); }
    });
    mkBtn('\u5217\u51fa\u7ffb\u8bd1\u670d\u52a1', async function(){
      try {
        var all = await new Promise(function(r){ chrome.storage.local.get(null, r); });
        var result = {};
        var keys = Object.keys(all).filter(function(k){
          var kl = k.toLowerCase();
          return kl.indexOf('custom') >= 0 || kl.indexOf('translation') >= 0 || kl.indexOf('service') >= 0 || kl.indexOf('translator') >= 0 || kl.indexOf('engine') >= 0 || kl.indexOf('ai') >= 0;
        }).slice(0, 50);
        keys.forEach(function(k){
          var v = all[k];
          result[k] = (typeof v === 'string' && v.length > 300) ? v.slice(0,300)+'...' : v;
        });
        result['__total_keys_in_storage__'] = Object.keys(all).length;
        addOutput(d, '\u7ffb\u8bd1\u670d\u52a1\u76f8\u5173 storage \u952e', result);
      } catch(e){ addOutput(d, '\u5217\u51fa\u5931\u8d25', e.message); }
    });
    mkBtn('\u6ce8\u5165\u6d4b\u8bd5 Custom AI', async function(){
      try {
        var url = prompt('API URL (\u5982 https://api.openai.com/v1/chat/completions):');
        if (!url) return;
        var key = prompt('API Key:');
        if (!key) return;
        var model = prompt('Model \u540d (\u5982 gpt-4o-mini \u6216 deepseek-chat):');
        if (!model) return;
        var name = prompt('\u5c55\u793a\u540d (\u968f\u4fbf\u5199):', 'MyCustomAI');
        if (!name) return;
        // Standard Custom AI config shape used by IMT
        var cfg = {
          url: url,
          apiKey: key,
          model: model,
          name: name,
          enabled: true,
          type: 'openai-custom',
          prompt: 'Please translate into to:\\n\\ntext',
          maxTextLengthPerRequest: 1000
        };
        // Try multiple known storage keys where IMT saves custom services
        var payload = {
          'custom-ai': cfg,
          'openai-custom': cfg,
          'userConfig.translationServices.custom-ai': cfg,
          'translationService': 'custom-ai',
          'translationServices.custom-ai.enabled': true
        };
        await new Promise(function(r){ chrome.storage.local.set(payload, r); });
        // Also read back and list the current full translationServices object if it exists
        var all = await new Promise(function(r){ chrome.storage.local.get(null, r); });
        addOutput(d, '\u5df2\u5199\u5165 storage\uff0c\u8bf7\u5237\u65b0 Options \u9875\u67e5\u770b\u662f\u5426\u51fa\u73b0\u5728\u7ffb\u8bd1\u670d\u52a1\u5217\u8868\u4e2d', {
          wrote: payload,
          current_related_keys: Object.keys(all).filter(function(k){ return k.toLowerCase().indexOf('custom') >= 0 || k.toLowerCase().indexOf('ai') >= 0; }).slice(0, 30)
        });
      } catch(e){ addOutput(d, '\u6ce8\u5165\u5931\u8d25', e.message); }
    });
    mkBtn('\u67e5\u770b\u7ffb\u8bd1\u9519\u8bef', function(){
      addOutput(d, 'fetch \u9519\u8bef\u65e5\u5fd7 (\u6700\u8fd1 30 \u6761)', errLog.slice(-30).length ? errLog.slice(-30) : '[\u7a7a - \u6682\u65e0 fetch \u5931\u8d25]');
    });
    mkBtn('\u91cd\u7f6e\u540c\u610f+\u89e3\u9501', function(){
      try {
        chrome.storage.local.set({hasAgreedCustomServiceConsent:true,hasAgreedCustomServiceConsent_v2:true,hasAgreed3rdPartyConsent:true,isPro:true,isMax:true,isVip:true,plan:'max',level:'max',subscription:{active:true,plan:'max',expiresAt:9999999999000}}, function(){ this.textContent = '\u5df2\u91cd\u7f6e'; }.bind(this));
      } catch(e){ this.textContent = 'FAIL: '+e.message; }
    });
    mkBtn('\u9690\u85cf', function(){ d.style.display = 'none'; try { document.body.style.paddingTop = ''; } catch(_){} });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
"""

def replace_v1_with_v2(path):
    with open(path, 'rb') as f:
        data = f.read()
    if TAG_V2_OPT in data:
        print('[skip] v2 already applied')
        return False
    if TAG_V1_OPT not in data:
        print('[ERR] v1 tag not found in', path)
        return False
    # Find the v1 IIFE: starts at TAG_V1_OPT, ends at the first '\n})();\n' after the tag
    start = data.index(TAG_V1_OPT)
    # Find matching '})();\n' after tag (the IIFE wrapping the v1 block)
    # v1 block ends with:  })();\n
    search_from = start
    end_marker = b'})();\n'
    # We need to find the '})();' that closes the outer IIFE of the v1 block.
    # Since v1 block content may contain nested })(), we instead look for the distinctive end
    # Actually v1 block does not contain nested })(); so first occurrence after start is correct.
    end = data.find(end_marker, search_from)
    if end < 0:
        print('[ERR] v1 end marker not found')
        return False
    end += len(end_marker)
    shutil.copy2(path, path + '.bak-mobile-rescue-v2')
    new = data[:start] + OPT_BLOCK_V2 + b'\n' + data[end:]
    with open(path, 'wb') as f:
        f.write(new)
    print('[ok] options.js v1 block replaced with v2: old=%d new=%d delta=%+d' % (len(data), len(new), len(new)-len(data)))
    return True

def main():
    os.chdir(ROOT)
    replace_v1_with_v2('options.js')
    print('done')

if __name__ == '__main__':
    main()
