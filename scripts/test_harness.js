// Test harness for kill_switch_core_v2.js + kill_switch_ui_v3.js + registry cleanup.
// Run with:  node patches/test_harness.js
'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert');

let passed = 0, failed = 0;
function t(name, fn){
  try {
    const r = fn();
    if (r && typeof r.then === 'function'){
      return r.then(()=>{ passed++; console.log('  \x1b[32mPASS\x1b[0m', name); },
                     e => { failed++; console.log('  \x1b[31mFAIL\x1b[0m', name, '-', e.message); });
    }
    passed++; console.log('  \x1b[32mPASS\x1b[0m', name);
  } catch(e){ failed++; console.log('  \x1b[31mFAIL\x1b[0m', name, '-', e.message); }
}
function section(n){ console.log('\n=== ' + n + ' ==='); }

// -------- Fake Chrome extension sandbox for core v2 --------
function makeSandbox(){
  const storageArea = (initial) => {
    const state = JSON.parse(JSON.stringify(initial||{}));
    return {
      get(keys, cb){
        let result = {};
        if (keys == null){ result = JSON.parse(JSON.stringify(state)); }
        else if (typeof keys === 'string'){ if (keys in state) result[keys] = state[keys]; }
        else if (Array.isArray(keys)){ keys.forEach(k => { if (k in state) result[k] = state[k]; }); }
        else if (typeof keys === 'object'){ for (const k in keys) result[k] = (k in state) ? state[k] : keys[k]; }
        if (cb){ setTimeout(()=>cb(result),0); return; }
        return Promise.resolve(result);
      },
      set(obj, cb){ Object.assign(state, obj); if (cb) cb(); return Promise.resolve(); },
      remove(k, cb){ const arr=Array.isArray(k)?k:[k]; arr.forEach(x=>delete state[x]); if(cb)cb(); return Promise.resolve(); },
      _state: state,
    };
  };

  // Minimal real fetch replacement: records calls, returns tagged response for "allow"
  const fetchCalls = [];
  async function realFetch(input, init){
    const url = (input && input.url) ? input.url : input;
    fetchCalls.push(url);
    return { __real: true, ok:true, status:200, url, json: async () => ({ real:true, url }) };
  }

  // Minimal XHR
  const xhrInstances = [];
  class FakeXHR {
    constructor(){
      this.readyState = 0; this.status = 0; this.statusText=''; this.response=''; this.responseText='';
      this.onreadystatechange = null; this.onload=null; this.onloadend=null; this.__listeners={};
      xhrInstances.push(this);
    }
    open(method, url){ this.__method=method; this.__url=url; this.readyState=1; }
    send(body){ this.__real_send_called = true; this.__body=body; /* real send: mark done */
      setTimeout(()=>{
        Object.defineProperty(this,'readyState',{value:4,configurable:true});
        Object.defineProperty(this,'status',{value:299,configurable:true});
        Object.defineProperty(this,'response',{value:'__real_xhr__',configurable:true});
        Object.defineProperty(this,'responseText',{value:'__real_xhr__',configurable:true});
        if(this.onload) this.onload();
      },0);
    }
    setRequestHeader(){}
    addEventListener(e,f){ (this.__listeners[e]=this.__listeners[e]||[]).push(f); }
    dispatchEvent(ev){ (this.__listeners[ev.type]||[]).forEach(f=>f(ev)); return true; }
  }

  const sandbox = {
    XMLHttpRequest: FakeXHR,
    Event: class Event { constructor(t){ this.type=t; } },
    navigator: { sendBeacon: (url, data) => { sandbox.__beaconCalls.push(url); return true; } },
    setTimeout, clearTimeout, Promise, Object, Array, JSON, String, URL, Math, Date,
    console,
    Response: global.Response || function(body, init){ this.body=body; this.status=(init&&init.status)||200; this.headers=(init&&init.headers)||{}; this.ok=this.status<400; this.text=()=>Promise.resolve(body); this.json=()=>Promise.resolve(JSON.parse(body)); },
    chrome: {
      runtime: { setUninstallURL: () => { sandbox.__uninstallCalled = true; return Promise.resolve(); } },
      storage: { local: storageArea({}), sync: storageArea({}), session: storageArea({}) },
    },
    browser: { runtime: { setUninstallURL: ()=>Promise.resolve() } },
    fetch: realFetch,
    __fetchCalls: fetchCalls,
    __xhrInstances: xhrInstances,
    __beaconCalls: [],
  };
  sandbox.self = sandbox;
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  return sandbox;
}

const vm = require('vm');
const v2src = fs.readFileSync(path.join(__dirname,'kill_switch_core_v2.js'),'utf8');

const sb = makeSandbox();
vm.createContext(sb);
vm.runInContext(v2src, sb);

(async () => {
  section('1. Global markers');
  t('__IMT_IS_PRO__ === true', () => assert.strictEqual(sb.__IMT_IS_PRO__, true));
  t('__IMT_IS_MAX__ === true', () => assert.strictEqual(sb.__IMT_IS_MAX__, true));
  t('__IMT_MOD_PRO_USER__.isPro === true', () => assert.strictEqual(sb.__IMT_MOD_PRO_USER__.isPro, true));
  t('__IMT_MOD_CORE_V2__ install guard set', () => assert.strictEqual(sb.__IMT_MOD_CORE_V2__, true));

  section('2. fetch: IMT first-party hosts → forged Pro envelope');
  const imtHosts = [
    'https://api.immersivetranslate.com/user/getUserInfo',
    'https://api2.immersivetranslate.cn/subscription',
    'https://aigw1.imtintl.com/v1/chat/completions',
    'https://immersive-translate.owenyoung.com/foo',
    'https://immersive-translate.deno.dev/bar',
    'https://imt-mod-null.invalid/x',
  ];
  for (const u of imtHosts){
    const r = await sb.fetch(u);
    const body = await r.json();
    t(`${u.replace(/^https?:\/\//,'')}: status 200 + isPro=true + plan=max`, () => {
      assert.strictEqual(r.status, 200);
      assert.strictEqual(body.isPro, true);
      assert.strictEqual(body.data.isPro, true);
      assert.strictEqual(body.data.isMax, true);
      assert.strictEqual(body.data.plan, 'max');
      assert.strictEqual(body.data.subscription.active, true);
      assert.strictEqual(body.data.features.aiSubtitle, true);
      assert.strictEqual(body.data.features.babelDoc, true);
      assert.strictEqual(body.data.features.mangaTranslate, true);
      assert.ok(body.data.quota.remaining > 1e9);
      assert.strictEqual(body.success, true);
      assert.strictEqual(body.code, 0);
    });
  }

  section('3. fetch: telemetry hosts → 204 empty');
  const telemetryHosts = [
    'https://www.google-analytics.com/collect',
    'https://analytics.google.com/g/collect',
    'https://www.googletagmanager.com/gtm.js',
    'https://openfpcdn.io/fingerprintjs/v3',
    'https://api.fpjs.io/events',
    'https://subhub.weixin.so/report',
  ];
  for (const u of telemetryHosts){
    const r = await sb.fetch(u);
    t(`${u.replace(/^https?:\/\//,'').slice(0,40)}: status 204`, () => assert.strictEqual(r.status, 204));
  }

  section('4. fetch: other hosts → passthrough to realFetch');
  sb.__fetchCalls.length = 0;
  const allowHosts = [
    'https://api.openai.com/v1/chat/completions',
    'https://generativelanguage.googleapis.com/v1/models',
    'https://api.anthropic.com/v1/messages',
    'https://openrouter.ai/api/v1',
    'https://127.0.0.1:11434/api/generate',
    'https://localhost:8080/translate',
    'https://api.deepseek.com/chat',
    'http://custom-llm.internal:8000/v1',
  ];
  for (const u of allowHosts){
    const r = await sb.fetch(u);
    t(`${u.slice(0,50)}: real fetch (no forge)`, () => {
      assert.strictEqual(r.__real, true);
      assert.ok(sb.__fetchCalls.includes(u));
    });
  }

  section('5. XHR behaviour');
  const xhrImt = new sb.XMLHttpRequest();
  xhrImt.open('GET', 'https://api.immersivetranslate.com/user');
  await new Promise(res => { xhrImt.onload = res; xhrImt.send(); });
  t('XHR IMT: status 200 + response JSON has isPro:true', () => {
    assert.strictEqual(xhrImt.status, 200);
    const body = JSON.parse(xhrImt.responseText);
    assert.strictEqual(body.isPro, true);
    assert.strictEqual(body.data.isMax, true);
    assert.strictEqual(xhrImt.__real_send_called, undefined, 'real send should NOT have been called');
  });

  const xhrTel = new sb.XMLHttpRequest();
  xhrTel.open('POST', 'https://www.google-analytics.com/collect');
  await new Promise(res => { xhrTel.onload = res; xhrTel.send('a=1'); });
  t('XHR telemetry: status 204 + real send not called', () => {
    assert.strictEqual(xhrTel.status, 204);
    assert.strictEqual(xhrTel.__real_send_called, undefined);
  });

  const xhrOk = new sb.XMLHttpRequest();
  xhrOk.open('POST', 'https://api.openai.com/v1');
  await new Promise(res => { xhrOk.onload = res; xhrOk.send('{}'); });
  t('XHR OpenAI: real send called, response untouched', () => {
    assert.strictEqual(xhrOk.__real_send_called, true);
    assert.strictEqual(xhrOk.response, '__real_xhr__');
  });

  section('6. sendBeacon');
  sb.__beaconCalls.length = 0;
  const b1 = sb.navigator.sendBeacon('https://www.google-analytics.com/collect', 'x');
  const b2 = sb.navigator.sendBeacon('https://api.immersivetranslate.com/log', 'x');
  const b3 = sb.navigator.sendBeacon('https://api.openai.com/v1', 'x');
  t('beacon telemetry: returns true but NOT sent', () => { assert.strictEqual(b1, true); assert.ok(!sb.__beaconCalls.includes('https://www.google-analytics.com/collect')); });
  t('beacon IMT: returns true but NOT sent', () => { assert.strictEqual(b2, true); assert.ok(!sb.__beaconCalls.includes('https://api.immersivetranslate.com/log')); });
  t('beacon allow host: real call recorded', () => { assert.strictEqual(b3, true); assert.ok(sb.__beaconCalls.includes('https://api.openai.com/v1')); });

  section('7. chrome.storage.get deep Pro injection');
  await sb.chrome.storage.local.set({
    userInfo: { isPro: false, isMax: false, plan: 'free', isTrial: true, subscription: { active: false, plan: 'free', expireAt: 0 } },
    somePref: { nested: { isPro: false, userType: 'free', level: 'free' } },
    unrelated: 'keep',
    subscription: { status: 'cancelled', active: false, plan: 'free' },
  });
  const got = await sb.chrome.storage.local.get(null);
  t('userInfo.isPro promoted to true', () => assert.strictEqual(got.userInfo.isPro, true));
  t('userInfo.isMax promoted to true', () => assert.strictEqual(got.userInfo.isMax, true));
  t('userInfo.plan promoted to "max"', () => assert.strictEqual(got.userInfo.plan, 'max'));
  t('userInfo.isTrial forced to false', () => assert.strictEqual(got.userInfo.isTrial, false));
  t('userInfo.subscription.active → true', () => assert.strictEqual(got.userInfo.subscription.active, true));
  t('userInfo.subscription.plan → max', () => assert.strictEqual(got.userInfo.subscription.plan, 'max'));
  t('nested isPro deep-merged', () => assert.strictEqual(got.somePref.nested.isPro, true));
  t('nested userType upgraded to max', () => assert.strictEqual(got.somePref.nested.userType, 'max'));
  t('nested level upgraded to max', () => assert.strictEqual(got.somePref.nested.level, 'max'));
  t('unrelated primitive preserved', () => assert.strictEqual(got.unrelated, 'keep'));
  t('top-level subscription.active → true', () => assert.strictEqual(got.subscription.active, true));
  t('top-level subscription.status → active', () => assert.strictEqual(got.subscription.status, 'active'));

  // Callback form
  await new Promise(res => sb.chrome.storage.local.get(['userInfo'], r => {
    t('callback form: userInfo.isPro injected', () => assert.strictEqual(r.userInfo.isPro, true));
    res();
  }));

  section('8. Uninstall URL stubbed');
  sb.chrome.runtime.setUninstallURL('https://example.com/uninstall-survey');
  t('setUninstallURL is a no-op (Promise resolves, no side-effect flag)', () => {
    assert.strictEqual(sb.__uninstallCalled, undefined);
  });

  section('9. Registry cleanup in default_config.json');
  const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'patched', 'default_config.json'),'utf8'));
  const dead = ['dpro','free-model','babel-lite-free','babel-lite-free.add_v.[1.23.9]','zhipu-pro','zhipu-pro.add_v.[1.15.3]','zhipu-air-pro','zhipu-air-pro.add_v.[1.20.12]','zhipu-base','zhipu-free'];
  const stillDead = dead.filter(k => k in cfg.translationServices);
  t('0 dead services remain in registry', () => assert.deepStrictEqual(stillDead, []));
  t('default translationService is bing', () => assert.strictEqual(cfg.translationService, 'bing'));
  t('BYOK services still present: openai/gemini/claude/deepseek/openrouter/ollama/zhipu/custom-ai', () => {
    ['openai','gemini','claude','deepseek','openrouter','ollama','zhipu','custom'].forEach(k => {
      assert.ok(k in cfg.translationServices, `missing BYOK: ${k}`);
    });
  });
  t('ai template kept but hidden', () => {
    assert.ok('ai' in cfg.translationServices);
    assert.strictEqual(cfg.translationServices.ai.hidden, true);
    assert.strictEqual(cfg.translationServices.ai.visible, false);
  });

  section('10. Bundle integrity: only v2 core, v1 removed');
  const bundles = ['background.js','content_guard.js','content_main.js','offscreen.js','options.js','popup.js','side-panel.js'];
  bundles.forEach(f => {
    const c = fs.readFileSync(path.join(__dirname, '..', 'patched', f),'utf8');
    t(`${f}: v1 marker absent`, () => assert.ok(!c.includes('IMT-MOD kill-switch core (prepended')));
    t(`${f}: v2 core present`, () => assert.ok(c.includes('__IMT_MOD_CORE_V2__')));
    t(`${f}: PRO_USER sentinel present`, () => assert.ok(c.includes('__IMT_MOD_PRO_USER__')));
    t(`${f}: /* IMT-MOD end */ sentinel removed`, () => assert.ok(!c.includes('/* IMT-MOD end */')));
  });
  ['options.js','popup.js','side-panel.js'].forEach(f => {
    const c = fs.readFileSync(path.join(__dirname, '..', 'patched', f),'utf8');
    t(`${f}: UI v3 DEAD_IDS present`, () => assert.ok(c.includes("'dpro'") && c.includes("'free-model'") && c.includes("'zhipu-pro'")));
    t(`${f}: UI v2 kill-switch present`, () => assert.ok(c.includes('__IMT_MOD_UI_V2__')));
    t(`${f}: UI v3 kill-switch present`, () => assert.ok(c.includes('__IMT_MOD_UI_V3__')));
  });

  section('11. Manifest integrity');
  const mf = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'patched', 'manifest.json'),'utf8'));
  t('manifest has no update_url', () => assert.ok(!('update_url' in mf)));
  t('manifest has no "key" (re-signed on load)', () => assert.ok(!('key' in mf)));
  t('manifest still has name', () => assert.ok(mf.name));

  console.log('\n==============================');
  console.log(`  \x1b[32m${passed} passed\x1b[0m   ${failed ? '\x1b[31m'+failed+' failed\x1b[0m' : '0 failed'}`);
  console.log('==============================');
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error('harness error:', e); process.exit(2); });
