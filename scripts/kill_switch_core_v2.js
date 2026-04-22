/* IMT-MOD kill-switch core v2 — block telemetry + forge "Pro forever" user info */
(function(){
  if (typeof self === 'undefined') return;
  var G = self;
  if (G.__IMT_MOD_CORE_V2__) return;
  G.__IMT_MOD_CORE_V2__ = true;

  // ---------- 1. Host lists ----------
  var TELEMETRY = [
    'google-analytics.com','analytics.google.com','googletagmanager.com',
    'openfpcdn.io','fpjs.dev','api.fpjs.io','fingerprintjs.com',
    'subhub.weixin.so'
  ];
  // IMT first-party hosts — we forge "Pro" responses instead of killing them
  var IMT = [
    'immersivetranslate.com','immersivetranslate.cn','imtintl.com',
    'immersive-translate.owenyoung.com','immersive-translate.deno.dev',
    'imt-mod-null.invalid'
  ];

  var FAR = 4102444800000; // 2100-01-01
  var PRO_USER = {
    id: 'imt-mod-pro', userId: 'imt-mod-pro', uid: 'imt-mod-pro',
    email: 'pro@local.invalid', nickname: 'Pro', username: 'Pro',
    avatar: '', phone: '', region: 'CN',
    isPro: true, isMax: true, isVip: true, isPaid: true, isPremium: true,
    isSubscribed: true, isTrial: false, trial: false,
    hasPro: true, hasVip: true, hasPremium: true, hasSubscription: true,
    pro: true, vip: true, premium: true,
    level: 'max', plan: 'max', planLevel: 'max', userLevel: 'max',
    userType: 'pro', accountType: 'pro', membershipLevel: 'max',
    subscriptionType: 'yearly', subscriptionStatus: 'active',
    status: 'active', state: 'active',
    expireAt: FAR, expiresAt: FAR, expiredAt: FAR, renewalDate: FAR,
    createdAt: 1700000000000, updatedAt: 1700000000000,
    subscription: {
      active: true, isActive: true, plan: 'max', level: 'max',
      type: 'pro', kind: 'max', status: 'active',
      expireAt: FAR, expiresAt: FAR, expiredAt: FAR, renewalDate: FAR,
      autoRenew: true, cancelled: false, canceledAt: 0
    },
    user: { isPro: true, isMax: true, plan: 'max', level: 'max' },
    account: { isPro: true, isMax: true, plan: 'max', level: 'max' },
    userInfo: { isPro: true, isMax: true, plan: 'max', level: 'max' },
    features: {
      pro: true, max: true, vip: true, ai: true, pdf: true, video: true,
      subtitle: true, manga: true, reward: true,
      aiWriting: true, selectionTranslation: true, aiAssistant: true,
      aiSubtitle: true, babelDoc: true, mangaTranslate: true,
      videoSubtitle: true, liveSubtitle: true, writingAssistant: true,
      quotaUnlimited: true
    },
    quota: { used: 0, total: 9e12, remaining: 9e12, hardLimit: 9e12 },
    usage: { used: 0, total: 9e12, remaining: 9e12, limit: 9e12 },
    limits: { total: 9e12, remaining: 9e12, used: 0 },
    balance: 9e12, points: 9e12, credits: 9e12
  };

  function envelope(){
    return {
      code: 0, status: 'ok', success: true, ok: true,
      msg: 'ok', message: 'ok', error: null,
      data: Object.assign({}, PRO_USER),
      result: Object.assign({}, PRO_USER),
      userInfo: Object.assign({}, PRO_USER),
      user: Object.assign({}, PRO_USER),
      subscription: Object.assign({}, PRO_USER.subscription),
      isPro: true, isMax: true, isVip: true, plan: 'max', level: 'max',
      quota: Object.assign({}, PRO_USER.quota),
      usage: Object.assign({}, PRO_USER.usage),
      list: [], items: [], total: 0, count: 0,
      // --- stop 'sync rules error' TypeError in content_main.js $d() ---
      // These fields are read by the cron sync-rules task; missing values crash .split().
      minVersion: '0.0.0',
      buildinConfigUpdatedAt: 0,
      // --- extra fallbacks for other code paths that may read from IMT hosts ---
      rule: { glossaries: [] },
      config: { glossaries: [], translationServices: {} },
      glossaries: [], translationServices: {},
      langsHash: {}, termsBaseUrl: '', buildinConfigSyncUrl: '',
      i18ns: {}, matches: [], excludeMatches: [],
      // terms sync
      syncTimestamp: 0, lastUserOpTime: 0,
      // reward / activity
      activities: [], rewards: [], popupMoreMenus: []
    };
  }

  // ---------- 2. URL classification ----------
  function classify(u){
    if (!u) return 'allow';
    var s = '';
    try { s = String(u); } catch(_){ return 'allow'; }
    if (!s || s[0] === '/' || s.indexOf('chrome-extension://') === 0
        || s.indexOf('moz-extension://') === 0
        || s.indexOf('data:') === 0 || s.indexOf('blob:') === 0
        || s.indexOf('about:') === 0) return 'allow';
    var low = s.toLowerCase();
    if (low.indexOf('localhost') !== -1 || low.indexOf('127.0.0.1') !== -1
        || low.indexOf('0.0.0.0') !== -1) return 'allow';
    for (var i=0;i<TELEMETRY.length;i++){
      if (low.indexOf(TELEMETRY[i]) !== -1) return 'telemetry';
    }
    for (var j=0;j<IMT.length;j++){
      if (low.indexOf(IMT[j]) !== -1) return 'imt';
    }
    return 'allow';
  }

  function jsonResponse(obj, status){
    status = status || 200;
    var noBody = (status === 204 || status === 205 || status === 304 || obj == null);
    var body = noBody ? null : JSON.stringify(obj);
    try {
      return new Response(body, {
        status: status,
        headers: body ? { 'content-type': 'application/json; charset=utf-8' } : {}
      });
    } catch(_){
      return { ok: status >= 200 && status < 400, status: status,
               json: function(){ return Promise.resolve(obj || {}); },
               text: function(){ return Promise.resolve(body || ''); } };
    }
  }

  // ---------- 3. Hook fetch ----------
  var origFetch = G.fetch && G.fetch.bind(G);
  if (origFetch){
    G.fetch = function(input, init){
      try {
        var url = (input && input.url) ? input.url : input;
        var cls = classify(url);
        if (cls === 'telemetry') return Promise.resolve(jsonResponse({}, 204));
        if (cls === 'imt')       return Promise.resolve(jsonResponse(envelope(), 200));
      } catch(_){}
      return origFetch(input, init);
    };
  }

  // ---------- 4. Hook XHR ----------
  try {
    var XHR = G.XMLHttpRequest;
    if (XHR && XHR.prototype){
      var origOpen = XHR.prototype.open;
      var origSend = XHR.prototype.send;
      XHR.prototype.open = function(method, url){
        this.__imtUrl = url;
        this.__imtCls = classify(url);
        return origOpen.apply(this, arguments);
      };
      XHR.prototype.send = function(){
        var self_ = this;
        if (this.__imtCls === 'telemetry' || this.__imtCls === 'imt'){
          var body = this.__imtCls === 'imt' ? JSON.stringify(envelope()) : '{}';
          var status = this.__imtCls === 'imt' ? 200 : 204;
          setTimeout(function(){
            try {
              Object.defineProperty(self_, 'readyState', {value:4, configurable:true});
              Object.defineProperty(self_, 'status',     {value:status, configurable:true});
              Object.defineProperty(self_, 'statusText', {value:'OK', configurable:true});
              Object.defineProperty(self_, 'responseURL',{value:String(self_.__imtUrl||''), configurable:true});
              Object.defineProperty(self_, 'response',     {value:body, configurable:true});
              Object.defineProperty(self_, 'responseText', {value:body, configurable:true});
              if (typeof self_.onreadystatechange === 'function') self_.onreadystatechange();
              if (typeof self_.onload === 'function') self_.onload();
              self_.dispatchEvent && self_.dispatchEvent(new Event('readystatechange'));
              self_.dispatchEvent && self_.dispatchEvent(new Event('load'));
              self_.dispatchEvent && self_.dispatchEvent(new Event('loadend'));
            } catch(_){}
          }, 0);
          return;
        }
        return origSend.apply(this, arguments);
      };
    }
  } catch(_){}

  // ---------- 5. Hook sendBeacon ----------
  try {
    if (G.navigator && G.navigator.sendBeacon){
      var origBeacon = G.navigator.sendBeacon.bind(G.navigator);
      G.navigator.sendBeacon = function(url){
        var cls = classify(url);
        if (cls !== 'allow') return true;
        return origBeacon.apply(G.navigator, arguments);
      };
    }
  } catch(_){}

  // ---------- 6. Stub uninstall URL ----------
  try {
    ['chrome','browser'].forEach(function(ns){
      if (self[ns] && self[ns].runtime && self[ns].runtime.setUninstallURL){
        self[ns].runtime.setUninstallURL = function(){ return Promise.resolve(); };
      }
    });
  } catch(_){}

  // ---------- 7. Storage: merge pro flags into every get() ----------
  function mergePro(obj, depth){
    if (!obj || depth > 8) return obj;
    if (Array.isArray(obj)) return obj.map(function(v){ return mergePro(v, depth+1); });
    if (typeof obj !== 'object') return obj;
    // Set boolean flags
    ['isPro','isMax','isVip','isPaid','isPremium','isSubscribed','hasPro','hasVip','hasPremium','hasSubscription','pro_user','vip_user','pro','vip','premium'].forEach(function(k){
      if (k in obj) obj[k] = true;
    });
    if ('isTrial' in obj) obj.isTrial = false;
    // Upgrade role strings
    ['userType','accountType','membershipLevel','userLevel','plan','plan_level','level','planLevel','subscriptionType','role'].forEach(function(k){
      if (k in obj && typeof obj[k] === 'string') obj[k] = 'max';
    });
    // Expand known containers
    ['subscription','user','userInfo','account'].forEach(function(k){
      if (obj[k] && typeof obj[k] === 'object'){
        obj[k].isPro = true; obj[k].isMax = true; obj[k].isVip = true;
        obj[k].active = true; obj[k].status = 'active';
        obj[k].plan = 'max'; obj[k].level = 'max';
        obj[k].expireAt = FAR; obj[k].expiresAt = FAR; obj[k].expiredAt = FAR;
      }
    });
    // Recurse
    Object.keys(obj).forEach(function(k){
      var v = obj[k];
      if (v && typeof v === 'object') obj[k] = mergePro(v, depth+1);
    });
    return obj;
  }

  try {
    ['chrome','browser'].forEach(function(ns){
      if (!self[ns] || !self[ns].storage) return;
      ['local','sync','session'].forEach(function(area){
        var s = self[ns].storage[area];
        if (!s || s.__imtModProGet) return;
        s.__imtModProGet = true;
        var origGet = s.get.bind(s);
        s.get = function(){
          var a = [].slice.call(arguments);
          var cb = typeof a[a.length-1] === 'function' ? a.pop() : null;
          var p = origGet.apply(s, a);
          var handle = function(res){
            try {
              // Only seed keys that were actually requested/returned
              if (res && typeof res === 'object'){
                return mergePro(res, 0);
              }
            } catch(_){}
            return res;
          };
          if (p && typeof p.then === 'function'){
            var wrapped = p.then(handle);
            if (cb) wrapped.then(cb, cb);
            return wrapped;
          }
          if (cb){
            return origGet.apply(s, a.concat([function(r){ cb(handle(r)); }]));
          }
          return p;
        };
      });
    });
  } catch(_){}

  // ---------- 8. Global pro markers ----------
  try {
    G.__IMT_IS_PRO__ = true;
    G.__IMT_IS_MAX__ = true;
    G.__IMT_MOD_PRO_USER__ = PRO_USER;
  } catch(_){}
})();
