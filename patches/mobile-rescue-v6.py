#!/usr/bin/env python3
# mobile-rescue v6: swallow dead-host fetch rejections in bg fetch hook.
#
# Root cause (from desktop F12 stack):
#   Ag (IMT's GA4 telemetry dispatcher, line 592) awaits fetch(u,i) for a
#   page_view event. We rewrote those URLs to imt-mod-null.invalid so the
#   fetch promise rejects with 'Failed to fetch'. The reject bubbles up
#   Ag -> yg -> sy -> Pd -> deliver -> routeMessage, killing the bg message
#   pipeline and the translation response never gets posted back.
#
# Fix: in the bg fetch hook (line 16 in background.js) intercept known dead
# hosts and return a stub 200 Response({}) so Ag's await resolves normally.
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, 'background.js')

OLD = (
    "  try{ var _f=self.fetch; self.fetch=function(){ var t0=Date.now(); var r=arguments[0]; var u=(typeof r==='string')?r:((r&&r.url)||'?'); var short=String(u).slice(0,180); return _f.apply(this,arguments).then(function(resp){ push('bg-fetch', resp.status, {u:short, ms:Date.now()-t0}); return resp; }).catch(function(e){ push('bg-fetch','THROW',{u:short, err:(e&&e.message)||String(e), ms:Date.now()-t0}); throw e; }); }; }catch(_){}\n"
)

NEW = (
    "  /* v6: swallow dead-host rejections to stop telemetry failures from killing translate deliver chain */\n"
    "  try{ var _f=self.fetch; var _DEADRE=/(imt-mod-null\\.invalid|analytics\\.immersivetranslate\\.com|api2\\.immersivetranslate\\.com|api2\\.imtintl\\.com|ai\\.immersivetranslate\\.com|config\\.immersivetranslate\\.com|immersivetranslate\\.com\\/mp\\/collect|google-analytics\\.com|googletagmanager\\.com|sentry\\.io|bugsnag\\.com)/i;\n"
    "    function _stub200(short){ try{ return new Response(JSON.stringify({ok:true,stub:true}), {status:200, headers:{'content-type':'application/json','x-imt-mod-stub':'1'}}); }catch(_){ return {ok:true,status:200,url:short,headers:new Headers(),clone:function(){return this;},text:function(){return Promise.resolve('{}');},json:function(){return Promise.resolve({ok:true,stub:true});},arrayBuffer:function(){return Promise.resolve(new ArrayBuffer(0));},blob:function(){return Promise.resolve(new Blob([]));}}; } }\n"
    "    self.fetch=function(){ var t0=Date.now(); var r=arguments[0]; var u=(typeof r==='string')?r:((r&&r.url)||'?'); var short=String(u).slice(0,180);\n"
    "      if (_DEADRE.test(short)) { push('bg-fetch','STUB',{u:short, ms:0}); return Promise.resolve(_stub200(short)); }\n"
    "      return _f.apply(this,arguments).then(function(resp){ push('bg-fetch', resp.status, {u:short, ms:Date.now()-t0}); return resp; }).catch(function(e){ push('bg-fetch','THROW',{u:short, err:(e&&e.message)||String(e), ms:Date.now()-t0}); if (_DEADRE.test(short)) return _stub200(short); throw e; });\n"
    "    }; }catch(_){}\n"
)

def main():
    with open(BG, 'rb') as f:
        data = f.read()
    if b'v6: swallow dead-host rejections' in data:
        print('[skip] v6 already applied')
        return
    old_b = OLD.encode('utf-8')
    if old_b not in data:
        print('[err] v3 bg fetch hook line not found', file=sys.stderr)
        sys.exit(1)
    bak = BG + '.bak-mobile-rescue-v6'
    if not os.path.exists(bak):
        shutil.copyfile(BG, bak)
    old_size = len(data)
    data = data.replace(old_b, NEW.encode('utf-8'), 1)
    with open(BG, 'wb') as f:
        f.write(data)
    print(f'[ok] background.js: {old_size} -> {len(data)} B ({len(data)-old_size:+d})')
    print('done')

if __name__=='__main__':
    main()
