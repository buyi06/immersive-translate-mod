#!/usr/bin/env python3
# extend-css-array.py
#
# Extend the __IMT_MOD_V3_HARDEN__ CSS array in all bundles that contain
# it. The original array has 6 entries targeting only classic paywall
# selectors. We add entries to also hide:
#   - Any <a>/<img>/<iframe> pointing at IMT first-party domains / hosts
#     (logos, promo images, referral landing pages, download prompts).
#   - Class/data-id substrings for invite / referral / reward / trial /
#     promo / coupon / discount / banner / paywall / locked.
#   - Elements labelled with 'vip-', 'premium-', 'trial-', etc.
#   - Leftover feature tiles that mark services as requiring a Pro plan
#     (\"pro-only\" / \"max-only\" labels).
#
# The array literal is byte-for-byte identical in every bundle that has
# the V3 harden header, so a single string replace handles all of them.
#
# Usage: python3 patches/extend-css-array.py [--apply]

import os, sys, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["options.js", "content_main.js", "background.js", "popup.js", "side-panel.js"]

OLD = (b"s.textContent = [\n"
       b"            \"a[href*='/pricing'],a[href*='/subscribe'],a[href*='/upgrade'],a[href*='/buy'],a[href*='/plans'],\",\n"
       b"            \"a[href*='AUTH_PRICING'],a[href*='utm_campaign=upgrade'],a[href*='utm_campaign=subscribe'],\",\n"
       b"            \"[data-id*='upgrade' i],[data-id*='pricing' i],[data-id*='subscribe' i],\",\n"
       b"            \"[class*='upgrade-' i],[class*='Upgrade' i],[class*='pricing-' i],[class*='subscribe-btn' i],\",\n"
       b"            \"[class*='UpgradeBtn' i],[class*='BuyPro' i],[class*='GetPro' i]\",\n"
       b"            \"{display:none !important;visibility:hidden !important;pointer-events:none !important;}\"\n"
       b"          ].join('');")

NEW = (b"s.textContent = [\n"
       b"            \"a[href*='/pricing'],a[href*='/subscribe'],a[href*='/upgrade'],a[href*='/buy'],a[href*='/plans'],\",\n"
       b"            \"a[href*='AUTH_PRICING'],a[href*='utm_campaign=upgrade'],a[href*='utm_campaign=subscribe'],\",\n"
       b"            \"a[href*='/checkout'],a[href*='/pay'],a[href*='/invite'],a[href*='/referral'],a[href*='/reward'],a[href*='/coupon'],a[href*='/discount'],a[href*='/download'],a[href*='/app-store'],a[href*='/google-play'],a[href*='/blog'],a[href*='/release-notes'],a[href*='/changelog'],\",\n"
       b"            \"a[href*='immersivetranslate.com'],a[href*='immersivetranslate.cn'],a[href*='imtintl.com'],a[href*='owenyoung.com'],a[href*='deno.dev/imt'],a[href*='immersive-translate.'],\",\n"
       b"            \"img[src*='immersivetranslate.com'],img[src*='immersivetranslate.cn'],img[src*='imtintl.com'],img[src*='owenyoung.com'],img[src*='immersive-translate.'],\",\n"
       b"            \"iframe[src*='immersivetranslate'],iframe[src*='imtintl'],iframe[src*='immersive-translate'],\",\n"
       b"            \"video[src*='immersivetranslate'],audio[src*='immersivetranslate'],source[src*='immersivetranslate'],\",\n"
       b"            \"[data-id*='upgrade' i],[data-id*='pricing' i],[data-id*='subscribe' i],[data-id*='invite' i],[data-id*='referral' i],[data-id*='reward' i],[data-id*='trial' i],[data-id*='coupon' i],[data-id*='discount' i],[data-id*='banner' i],[data-id*='paywall' i],[data-id*='promo' i],\",\n"
       b"            \"[class*='upgrade-' i],[class*='Upgrade' i],[class*='pricing-' i],[class*='subscribe-btn' i],[class*='UpgradeBtn' i],[class*='BuyPro' i],[class*='GetPro' i],\",\n"
       b"            \"[class*='paywall' i],[class*='premium-' i],[class*='premium_' i],[class*='vip-' i],[class*='vip_' i],[class*='trial-' i],[class*='trial_' i],[class*='coupon' i],[class*='discount' i],[class*='invite' i],[class*='referral' i],[class*='reward' i],[class*='promo' i],[class*='banner' i],[class*='announcement' i],[class*='share-card' i],[class*='ShareCard' i],\",\n"
       b"            \"[class*='need-pro' i],[class*='NeedPro' i],[class*='pro-only' i],[class*='ProOnly' i],[class*='max-only' i],[class*='MaxOnly' i],[class*='lock-' i],[class*='locked-' i],\",\n"
       b"            \"[class*='download-app' i],[class*='DownloadApp' i],[class*='app-store' i],[class*='google-play' i],[class*='mobile-promo' i],[class*='AppPromo' i]\",\n"
       b"            \"{display:none !important;visibility:hidden !important;pointer-events:none !important;}\"\n"
       b"          ].join('');")


def main():
    apply = "--apply" in sys.argv
    for name in FILES:
        path = os.path.join(ROOT, name)
        with open(path, "rb") as fh:
            data = fh.read()
        count = data.count(OLD)
        if count != 1:
            print(f"[{name}] SKIP: expected 1 match of original array, got {count}")
            continue
        new_data = data.replace(OLD, NEW, 1)
        delta = len(new_data) - len(data)
        print(f"[{name}] match ok; delta = {delta:+d} B; {len(data)} -> {len(new_data)}")
        if apply:
            bak = path + ".bak-css-extend"
            if not os.path.exists(bak):
                shutil.copy2(path, bak)
                print(f"  backup -> {bak}")
            with open(path, "wb") as fh:
                fh.write(new_data)
            print(f"  wrote {path}")


if __name__ == "__main__":
    main()
