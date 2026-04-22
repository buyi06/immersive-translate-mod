#!/usr/bin/env python3
"""
fix_ui_gates.py

Remove three remaining paywall/consent UI gates from options.js (Pro user
enforcement and third-party API compliance dialog):

  1. "使用须知" compliance modal (function wL in options.js) -> auto-confirm + render null
  2. YouTube "AI 智能分句" (subtitle.ytAIAsr) lock -> always visible and enabled
  3. "添加自定义翻译服务" picker missing Custom AI / OpenAI / Claude / Gemini ...
     -> drop the ny(...) per-user gate so every BYOK service (Dn[s].allProps.length>0) shows up

All three live exclusively inside options.js. Everything else stays untouched.
"""
import re, sys, pathlib

ROOT    = pathlib.Path('/root/projects/linux-audit/immersive-translate-mod-repo')
TARGET  = ROOT / 'options.js'


def balanced_block_end(src: str, start_open: int) -> int:
    """Given offset of '{' return offset one past matching '}', skipping
    strings/regexes/comments (simple state machine)."""
    assert src[start_open] == '{'
    depth = 0
    i = start_open
    n = len(src)
    while i < n:
        ch = src[i]
        # comment
        if ch == '/' and i+1 < n and src[i+1] in ('/', '*'):
            if src[i+1] == '/':
                j = src.find('\n', i+2)
                i = n if j == -1 else j+1
                continue
            j = src.find('*/', i+2)
            i = n if j == -1 else j+2
            continue
        # strings
        if ch in ('"', "'", '`'):
            q = ch
            i += 1
            while i < n:
                c = src[i]
                if c == '\\':
                    i += 2
                    continue
                if c == q:
                    i += 1
                    break
                if q == '`' and c == '$' and i+1 < n and src[i+1] == '{':
                    # template literal expression - recurse
                    end = balanced_block_end(src, i+1)
                    i = end
                    continue
                i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise RuntimeError('unbalanced braces')


def patch_wL(src: str) -> tuple[str, bool]:
    """Replace the body of `function wL(e){...}` so it auto-confirms and renders null."""
    m = re.search(r'function wL\(e\)\{', src)
    if not m:
        return src, False
    # guard: only rewrite if body still references the consent i18n keys
    body_open = m.end() - 1
    body_end = balanced_block_end(src, body_open)
    body = src[body_open:body_end]
    if 'services.consent.title' not in body and 'services.consent.requiredText' not in body:
        return src, False
    stub = '{var _r=e&&e.onConfirm;if(e&&e.visible&&typeof _r==="function"){try{_r()}catch(_){}}return null;}'
    return src[:body_open] + stub + src[body_end:], True


def patch_ytAIAsr(src: str) -> tuple[str, int]:
    """Force the YouTube AI Smart-Split nav always visible and its toggle enabled."""
    changes = 0
    # 1) wrapper visibility: hidden:Zt(t,e.isPro) -> hidden:!1
    old_hidden = 'hidden:Zt(t,e.isPro),children:[u(Ee,{title:r("subtitle.ytAIAsr")'
    new_hidden = 'hidden:!1,children:[u(Ee,{title:r("subtitle.ytAIAsr")'
    if old_hidden in src:
        src = src.replace(old_hidden, new_hidden, 1)
        changes += 1
    # 2) disabled gate and upsell tooltip
    old_tip = 'disableTipText:e.isPro?r("subtitle.ytAsrDisableTooltip"):r("onlyProUseProTooltip",{1:U.GO_USER_PROFILE_WITH_YT_AI_ASR})'
    new_tip = 'disableTipText:r("subtitle.ytAsrDisableTooltip")'
    if old_tip in src:
        src = src.replace(old_tip, new_tip, 1)
        changes += 1
    old_dis = 'disabled:!t.generalRule.subtitleRule.preTranslation||!e.isPro,onChange:'
    new_dis = 'disabled:!t.generalRule.subtitleRule.preTranslation,onChange:'
    if old_dis in src:
        src = src.replace(old_dis, new_dis, 1)
        changes += 1
    return src, changes


def patch_BX(src: str) -> tuple[str, bool]:
    """Make every BYOK service (任何带 allProps 的内置服务) show up in 添加自定义翻译服务 picker."""
    old = '.filter(s=>!Dn[s].allProps?.length||["zhipu-pro","qwen"].includes(s)?!1:ny({serviceKey:s,ctx:e.ctx}))'
    new = '.filter(s=>!(!Dn[s].allProps?.length||["zhipu-pro","qwen"].includes(s)))'
    if old not in src:
        return src, False
    return src.replace(old, new, 1), True


def main() -> int:
    src = TARGET.read_text(encoding='utf-8')
    original_len = len(src)

    src, ok_wL = patch_wL(src)
    print(f'  [wL compliance popup]   {"ok" if ok_wL else "skip (not found / already patched)"}')

    src, n_yt = patch_ytAIAsr(src)
    print(f'  [ytAIAsr lock]          {n_yt}/3 replacements applied')

    src, ok_bx = patch_BX(src)
    print(f'  [BX add-service list]   {"ok" if ok_bx else "skip (not found / already patched)"}')

    if not (ok_wL or n_yt or ok_bx):
        print('nothing to do')
        return 1

    TARGET.write_text(src, encoding='utf-8')
    print(f'  options.js size: {original_len} -> {len(src)} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
