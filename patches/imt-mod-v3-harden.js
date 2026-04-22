/* IMT-MOD kill-switch v3 — Request hook + error swallow + sendMessage wrapper */
(function(){
  if (typeof self === 'undefined') return;
  var G = self;
  if (G.__IMT_MOD_V3_HARDEN__) return;
  G.__IMT_MOD_V3_HARDEN__ = true;

  var IMT_RE   = /(immersivetranslate\.(?:com|cn)|imtintl\.com|immersive-translate\.(?:owenyoung\.com|deno\.dev)|imt-mod-null\.invalid)/i;
  var TELEM_RE = /(google-analytics|analytics\.google|googletagmanager|openfpcdn|fpjs|fingerprint|subhub\.weixin)/i;

  // ---------- 1. Hook Request constructor (covers `new Request(url).clone().url` patterns) ----------
  try {
    var OrigRequest = G.Request;
    if (OrigRequest && !OrigRequest.__imtWrapped) {
      var WrappedRequest = function(input, init){
        try {
          var u = typeof input === 'string' ? input : (input && input.url);
          if (u && (IMT_RE.test(u) || TELEM_RE.test(u))) {
            return Reflect.construct(OrigRequest, ['data:application/json,%7B%7D', init || {}]);
          }
        } catch(_){}
        return Reflect.construct(OrigRequest, [input, init]);
      };
      WrappedRequest.__imtWrapped = true;
      WrappedRequest.prototype = OrigRequest.prototype;
      try { G.Request = WrappedRequest; } catch(_){}
    }
  } catch(_){}

  // ---------- 2. Swallow benign runtime errors ----------
  var BENIGN = [
    /Could not establish connection/i,
    /Receiving end does not exist/i,
    /The message port closed before/i,
    /Extension context invalidated/i,
    /Cannot read properties of null \(reading 'startsWith'\)/i,
    /Cannot read properties of undefined \(reading 'startsWith'\)/i,
    /reading 'sendMessage'/i,
    /reading 'connect'/i
  ];
  function isBenign(msg){
    if (!msg) return false;
    var s = '';
    try { s = typeof msg === 'string' ? msg : (msg.message || JSON.stringify(msg)); } catch(_){}
    for (var i=0;i<BENIGN.length;i++) if (BENIGN[i].test(s)) return true;
    return false;
  }
  try {
    if (G.addEventListener) {
      G.addEventListener('error', function(e){
        try {
          var m = (e && (e.message || (e.error && (e.error.message || e.error)))) || '';
          if (isBenign(m)) {
            e.preventDefault && e.preventDefault();
            e.stopImmediatePropagation && e.stopImmediatePropagation();
            return false;
          }
        } catch(_){}
      }, true);
      G.addEventListener('unhandledrejection', function(e){
        try {
          var reason = e && e.reason;
          var m = reason && (reason.message || reason) || '';
          if (isBenign(m)) {
            e.preventDefault && e.preventDefault();
            e.stopImmediatePropagation && e.stopImmediatePropagation();
            return false;
          }
        } catch(_){}
      }, true);
    }
  } catch(_){}

  // ---------- 3. Wrap chrome.runtime.sendMessage / connect to never throw benign errors ----------
  try {
    ['chrome','browser'].forEach(function(ns){
      var api = G[ns];
      if (!api || !api.runtime) return;
      var r = api.runtime;
      if (r.__imtWrapped) return;
      r.__imtWrapped = true;

      if (typeof r.sendMessage === 'function') {
        var origSM = r.sendMessage.bind(r);
        r.sendMessage = function(){
          var args = [].slice.call(arguments);
          var cb = null;
          if (args.length && typeof args[args.length-1] === 'function') cb = args.pop();
          try {
            var ret = origSM.apply(null, cb ? args.concat([function(resp){
              try { var le = api.runtime && api.runtime.lastError; if (le && isBenign(le.message)) { /* swallow */ } } catch(_){}
              try { cb(resp); } catch(_){}
            }]) : args);
            if (ret && typeof ret.then === 'function') {
              return ret.catch(function(err){
                if (isBenign(err && err.message)) return undefined;
                throw err;
              });
            }
            return ret;
          } catch(e) {
            if (isBenign(e && e.message)) return cb ? undefined : Promise.resolve(undefined);
            throw e;
          }
        };
      }

      if (typeof r.connect === 'function') {
        var origConnect = r.connect.bind(r);
        r.connect = function(){
          try { return origConnect.apply(null, arguments); }
          catch(e) {
            if (isBenign(e && e.message)) {
              // return a no-op port
              return { name:'imt-mod-noop', onMessage:{addListener:function(){},removeListener:function(){}}, onDisconnect:{addListener:function(){},removeListener:function(){}}, postMessage:function(){}, disconnect:function(){} };
            }
            throw e;
          }
        };
      }
    });
  } catch(_){}

  // ---------- 4. CSS guard: hide any residual upgrade / pricing / subscribe UI ----------
  try {
    if (G.document && G.document.documentElement) {
      var applyCss = function(){
        try {
          if (G.document.getElementById('imt-mod-v3-css')) return;
          var s = G.document.createElement('style');
          s.id = 'imt-mod-v3-css';
          s.textContent = [
            "a[href*='/pricing'],a[href*='/subscribe'],a[href*='/upgrade'],a[href*='/buy'],a[href*='/plans'],",
            "a[href*='AUTH_PRICING'],a[href*='utm_campaign=upgrade'],a[href*='utm_campaign=subscribe'],",
            "[data-id*='upgrade' i],[data-id*='pricing' i],[data-id*='subscribe' i],",
            "[class*='upgrade-' i],[class*='Upgrade' i],[class*='pricing-' i],[class*='subscribe-btn' i],",
            "[class*='UpgradeBtn' i],[class*='BuyPro' i],[class*='GetPro' i]",
            "{display:none !important;visibility:hidden !important;pointer-events:none !important;}"
          ].join('');
          (G.document.head || G.document.documentElement).appendChild(s);
        } catch(_){}
      };
      if (G.document.readyState === 'loading') {
        G.document.addEventListener('DOMContentLoaded', applyCss, { once:true });
      } else {
        applyCss();
      }
    }
  } catch(_){}
})();
