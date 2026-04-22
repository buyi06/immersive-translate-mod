/* IMT-MOD UI kill-switch v3 — hide first-party translator services from pickers */
(function(){
  if (typeof document === 'undefined') return;
  if (window.__IMT_MOD_UI_V3__) return;
  window.__IMT_MOD_UI_V3__ = true;

  var DEAD_IDS = [
    'dpro','free-model',
    'babel-lite-free','babel-lite',
    'zhipu-pro','zhipu-air-pro','zhipu-base','zhipu-free'
  ];

  // Build a CSS selector list that targets <option>, list items, buttons and
  // any element tagged with one of the dead service IDs via common attributes.
  var ATTRS = ['value','data-value','data-service','data-service-id','data-id','data-key','data-name','data-translator','data-translation-service'];
  var selectors = [];
  DEAD_IDS.forEach(function(id){
    ATTRS.forEach(function(a){
      selectors.push('['+a+'="'+id+'"]');
    });
    // href anchors
    selectors.push('[href*="service='+id+'" i]');
  });
  // Also hide list rows / option items that textContent matches the IMT-official
  // model product names exactly. Use class/id hints + short textual match below.
  var css = selectors.join(',')+'{display:none!important;visibility:hidden!important;pointer-events:none!important;height:0!important;width:0!important;margin:0!important;padding:0!important;overflow:hidden!important}';

  function inject(){
    if (!document.head) return;
    var sid = 'imt-mod-ui-hide-v3';
    if (document.getElementById(sid)) return;
    var s = document.createElement('style');
    s.id = sid; s.textContent = css;
    document.head.appendChild(s);
  }
  inject();
  new MutationObserver(function(){
    if (!document.getElementById('imt-mod-ui-hide-v3')) inject();
  }).observe(document.documentElement, {childList:true, subtree:true});

  // Scan for <option> elements whose value is a dead ID and remove them from
  // the select (so native <select> dropdowns don't render an empty slot).
  function purgeOptions(root){
    try {
      var opts = (root || document).querySelectorAll('option');
      for (var i=0;i<opts.length;i++){
        if (DEAD_IDS.indexOf(opts[i].value) !== -1){
          opts[i].remove();
        }
      }
    } catch(_){}
  }
  purgeOptions();
  new MutationObserver(function(muts){
    for (var i=0;i<muts.length;i++){
      muts[i].addedNodes && muts[i].addedNodes.forEach(function(n){
        if (n.nodeType === 1) purgeOptions(n);
      });
    }
  }).observe(document.documentElement, {childList:true, subtree:true});

  // Strip dead IDs from storage reads so the rest of the app never "sees" them.
  // This layers on top of the v1 core wrapper (which already merged PRO_FLAGS).
  try {
    function stripDead(obj, depth){
      if (!obj || depth > 6) return obj;
      if (Array.isArray(obj)){
        var out = [];
        for (var i=0;i<obj.length;i++){
          if (DEAD_IDS.indexOf(obj[i]) !== -1) continue;
          out.push(stripDead(obj[i], depth+1));
        }
        return out;
      }
      if (typeof obj === 'object'){
        var keys = Object.keys(obj);
        for (var j=0;j<keys.length;j++){
          var k = keys[j];
          if (DEAD_IDS.indexOf(k) !== -1){ try { delete obj[k]; } catch(_){} continue; }
          obj[k] = stripDead(obj[k], depth+1);
        }
        // Swap default-selected service away from dead IDs
        ['translationService','clientImageTranslationService','inputTranslationService','selectedService','currentService'].forEach(function(f){
          if (DEAD_IDS.indexOf(obj[f]) !== -1) obj[f] = 'bing';
        });
        return obj;
      }
      return obj;
    }
    ['chrome','browser'].forEach(function(ns){
      try {
        if (!self[ns] || !self[ns].storage) return;
        ['local','sync','session'].forEach(function(area){
          var s = self[ns].storage[area];
          if (!s || s.__imtModDeadStripped) return;
          s.__imtModDeadStripped = true;
          var origGet = s.get.bind(s);
          s.get = function(){
            var a = [].slice.call(arguments);
            var cb = typeof a[a.length-1] === 'function' ? a.pop() : null;
            var p = origGet.apply(s, a);
            var handle = function(res){
              try { return stripDead(res, 0); } catch(_){ return res; }
            };
            if (p && typeof p.then === 'function'){
              var wrapped = p.then(handle);
              if (cb) wrapped.then(cb, cb);
              return wrapped;
            }
            if (cb){
              return origGet.apply(s, a.concat([function(res){ cb(handle(res)); }]));
            }
            return p;
          };
        });
      } catch(_){}
    });
  } catch(_){}
})();
