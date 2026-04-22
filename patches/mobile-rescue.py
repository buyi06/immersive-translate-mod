#!/usr/bin/env python3
# IMT-MOD mobile rescue patch
# Adds:
#   1. Service Worker keep-alive (alarms @ ~21s) to background.js
#   2. Storage pre-seed (hasAgreedCustomServiceConsent/isPro/etc) on startup/install/startup
#   3. runtime.onMessage 'imt-mod-ping' handler for options-page self-check
#   4. Visible debug banner on options.html (user-readable, no F12 needed)
#
# Idempotent: uses IMT_MOD_MOBILE_RESCUE_TAG sentinel in each file.

import os, sys, time, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG_BG  = b'/* IMT-MOD MOBILE RESCUE bg v1 */'
TAG_OPT = b'/* IMT-MOD MOBILE RESCUE opt v1 */'

BG_BLOCK = b"""/* IMT-MOD MOBILE RESCUE bg v1 */
(function(){
  if (typeof self === 'undefined') return;
  if (self.__IMT_MOD_MOBILE_RESCUE__) return;
  self.__IMT_MOD_MOBILE_RESCUE__ = true;
  var SEED = {
    hasAgreedCustomServiceConsent: true,
    hasAgreedCustomServiceConsent_v2: true,
    hasAgreedCustomServiceConsent_v3: true,
    hasAgreed3rdPartyConsent: true,
    hasAgreedPrivacyPolicy: true,
    isPro: true, isMax: true, isVip: true, isPremium: true,
    plan: 'max', level: 'max', membership: 'max',
    subscription: { active: true, plan: 'max', level: 'max', expiresAt: 9999999999000 },
    user: { id: 'local', plan: 'max', isPro: true, isMax: true, isVip: true, active: true },
    imt_mod_ready: true,
    imt_mod_ready_ts: Date.now(),
    imt_mod_rescue_v: 1
  };
  function seed(){ try { chrome.storage.local.set(SEED, function(){}); } catch(_){} try { chrome.storage.sync && chrome.storage.sync.set(SEED, function(){}); } catch(_){} }
  // 1) Seed immediately at SW boot
  try { seed(); } catch(_){}
  // 2) Re-seed on install/startup
  try { chrome.runtime.onInstalled && chrome.runtime.onInstalled.addListener(function(){ seed(); }); } catch(_){}
  try { chrome.runtime.onStartup && chrome.runtime.onStartup.addListener(function(){ seed(); }); } catch(_){}
  // 3) Keep-alive via alarms (~21 seconds -> below the 30s MV3 idle threshold)
  try {
    if (chrome.alarms && chrome.alarms.create) {
      chrome.alarms.create('imt-mod-keepalive', { periodInMinutes: 0.35 });
      chrome.alarms.onAlarm.addListener(function(a){
        if (a && a.name === 'imt-mod-keepalive') {
          try { chrome.runtime.getPlatformInfo(function(){}); } catch(_){}
          try { chrome.storage.local.get('imt_mod_ready', function(){}); } catch(_){}
        }
      });
    }
  } catch(_){}
  // 4) Ping responder for options-page self-check
  try {
    chrome.runtime.onMessage.addListener(function(msg, sender, reply){
      if (msg && msg.type === 'imt-mod-ping') {
        try { seed(); } catch(_){}
        try { reply({ ok:true, ts: Date.now(), rescue:1, v:1 }); } catch(_){}
        return true;
      }
    });
  } catch(_){}
})();
"""

OPT_BLOCK = b"""/* IMT-MOD MOBILE RESCUE opt v1 */
(function(){
  if (typeof self === 'undefined') return;
  if (self.__IMT_MOD_MOBILE_RESCUE_OPT__) return;
  self.__IMT_MOD_MOBILE_RESCUE_OPT__ = true;
  function mount(){
    try {
      if (!document.body) { setTimeout(mount, 50); return; }
      if (document.getElementById('imt-mod-banner')) return;
      var st = document.createElement('style');
      st.textContent = '#imt-mod-banner{position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#0b6;color:#fff;font:12px/1.4 ui-monospace,Menlo,monospace;padding:8px 10px;box-shadow:0 2px 8px rgba(0,0,0,.25);white-space:pre-wrap;word-break:break-all;max-height:50vh;overflow:auto}#imt-mod-banner .imt-mod-fail{background:#c33;color:#fff;padding:1px 4px;border-radius:2px}#imt-mod-banner button{margin:6px 6px 0 0;background:#073;color:#fff;border:0;padding:4px 9px;border-radius:3px;font:11px monospace;cursor:pointer}';
      document.head.appendChild(st);
      var d = document.createElement('div');
      d.id = 'imt-mod-banner';
      d.textContent = 'IMT-MOD diagnostics ...';
      document.body.appendChild(d);
      // push page content down so banner does not cover UI
      try { document.body.style.paddingTop = '10px'; } catch(_){}
      run(d);
    } catch(e){ try { console.error('[imt-mod-opt-banner]', e); } catch(_){} }
  }
  function line(d, t){ d.appendChild(document.createElement('br')); d.appendChild(document.createTextNode(t)); }
  async function run(d){
    d.textContent = '=== IMT-MOD \u624b\u673a\u81ea\u68c0 ===';
    line(d, 'V3_HARDEN: ' + !!self.__IMT_MOD_V3_HARDEN__);
    var cssEl = document.getElementById('imt-mod-v3-css');
    line(d, 'CSS inject: ' + (cssEl ? 'YES ('+ (cssEl.textContent.match(/\\{/g)||[]).length +' rules)' : 'NO'));
    line(d, 'CSS has imtintl.com: ' + (cssEl && cssEl.textContent.indexOf('imtintl.com') >= 0));
    try { var mf = chrome.runtime.getManifest(); line(d, 'Ext: '+mf.name+' v'+mf.version+' id='+chrome.runtime.id); }
    catch(e){ line(d, 'manifest err: '+e.message); }
    try {
      var pong = await new Promise(function(r, rj){
        var done = false;
        setTimeout(function(){ if(!done) rj(new Error('timeout 5s \u2013 SW did not respond')); }, 5000);
        try { chrome.runtime.sendMessage({type:'imt-mod-ping'}, function(resp){ done = true; if (chrome.runtime.lastError) { rj(new Error(chrome.runtime.lastError.message||'lastError')); } else { r(resp); } }); }
        catch(err){ done = true; rj(err); }
      });
      line(d, 'SW ping: OK \u2013 '+JSON.stringify(pong));
    } catch(e){
      var span = document.createElement('span'); span.className = 'imt-mod-fail'; span.textContent = 'SW ping: FAIL \u2013 '+e.message+'  [\u624b\u673a MV3 SW \u6ca1\u8d77!]';
      d.appendChild(document.createElement('br')); d.appendChild(span);
    }
    try {
      var s = await new Promise(function(r){ chrome.storage.local.get(['hasAgreedCustomServiceConsent','isPro','imt_mod_ready','imt_mod_ready_ts','imt_mod_rescue_v'], r); });
      line(d, 'storage: '+JSON.stringify(s));
    } catch(e){ line(d, 'storage FAIL: '+e.message); }
    // buttons
    d.appendChild(document.createElement('br'));
    var copy = document.createElement('button'); copy.textContent = '\u590d\u5236\u8bca\u65ad';
    copy.onclick = function(){ try { navigator.clipboard.writeText(d.textContent); copy.textContent = '\u5df2\u590d\u5236'; } catch(_){ var ta = document.createElement('textarea'); ta.value = d.textContent; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); copy.textContent = '\u5df2\u590d\u5236'; } catch(__){} document.body.removeChild(ta); } };
    d.appendChild(copy);
    var reseed = document.createElement('button'); reseed.textContent = '\u91cd\u7f6e\u540c\u610f\u72b6\u6001+\u89e3\u9501';
    reseed.onclick = async function(){
      try {
        chrome.storage.local.set({hasAgreedCustomServiceConsent:true,hasAgreedCustomServiceConsent_v2:true,hasAgreed3rdPartyConsent:true,isPro:true,isMax:true,isVip:true,plan:'max',level:'max',subscription:{active:true,plan:'max',expiresAt:9999999999000}}, function(){ reseed.textContent = '\u5df2\u91cd\u7f6e\uff0c\u91cd\u542f\u6269\u5c55'; });
      } catch(e){ reseed.textContent = 'FAIL: '+e.message; }
    };
    d.appendChild(reseed);
    var hide = document.createElement('button'); hide.textContent = '\u9690\u85cf';
    hide.onclick = function(){ d.style.display = 'none'; try { document.body.style.paddingTop = ''; } catch(_){} };
    d.appendChild(hide);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
"""

def patch(path, tag, block):
    with open(path, 'rb') as f:
        data = f.read()
    if tag in data:
        print(f'[skip] {path} already patched')
        return False, len(data)
    backup = path + '.bak-mobile-rescue'
    shutil.copy2(path, backup)
    new = block + b'\n' + data
    with open(path, 'wb') as f:
        f.write(new)
    print(f'[ok]   {path}: +{len(new) - len(data)} B (new size {len(new)} B)')
    return True, len(new)

def main():
    os.chdir(ROOT)
    patch('background.js', TAG_BG, BG_BLOCK)
    patch('options.js',    TAG_OPT, OPT_BLOCK)
    # Also patch popup.js & side-panel.js so they benefit from keep-alive + seed messaging
    # (same background-style block is safe in content/page contexts; only adds ping handler that listener stays unused)
    # but banner is options-only, so do NOT add OPT block there.
    print('done')

if __name__ == '__main__':
    main()
