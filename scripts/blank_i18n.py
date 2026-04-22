#!/usr/bin/env python3
"""Blank out i18n keys for paid/login/reward/sync/donate across all languages in locales.json."""
import json, re, sys

SRC = 'patched/locales.json'

# Exact keys
EXACT = {
    # Login / account
    'login','logout','nologin','notLogin','notLoginPro','goLogin','goLoginOrAction',
    'loginForSafari','manageAccount','currentAccount','openPremium',
    # Sync / cloud
    'syncToAccount','syncToAccountButton','syncToAccountDescription',
    'successSyncConfigInAccount','successSyncConfigToAccount','uploadFail',
    # Donate / feedback / community
    'donateCafe','feedback','feedbackAndJoin','feedbackOrMore',
    'reportInfo.tip','reportTip','reportInfo.email','reportInfo.emailError',
    'reportInfo.emailEmptyMsg','reportInfo.emailPlaceholder','subscribeEmail',
    'wechatPublicAccount','wechatCommunities','customerServiceWeChat',
    'translationServices.wechat','projectHomepage',
    # Pro / upgrade direct
    'upgradeToPro','upgradeToProWithProfile','upgradeToProErrorTitle','clickUpgradePro',
    'popup.upgrade','popup.openPro','popup.openProForPro','popup.trial_pro_service',
    'floatBall.upgrade','freeImage.upgradeToProText','onlyProUseProTooltip',
    'proRightOpenPro','proRightDescription',
    'subtitle.upgradePro','subtitle.upgradeProMessage',
    'subtitle.upgradeProMessage.downloadSubtitle','subtitle.quickButton.upgradePro',
    'subtitle.quickButton.liveOnlyPro','subtitle.liveFreeTrialTip','subtitle.liveFreeTrialEndTip',
    'subtitle.error.aiSubtitleLimitFree','subtitle.error.aiSubtitleProOnly',
    'guide.mangaProTip','guide.mangaNoProTip',
    'services.upgradeProUseModel','services.upgradeMaxUseModel',
    'translationServices.upgradePro','translationServices.upgradeMax',
    'translationServices.upgradeMaxUser','translationServices.proOnly',
    'translationServices.proUserDirectUse','translationServices.free-model',
    'translationServicesGroup.pro','translationServicesGroup.free',
    'translationServices.dpro','translationServices.dpro.introduction',
    'translationServices.zhipu-pro','translationServices.zhipu-pro.introduction',
    # Plan badges
    'freePlan','autoRenewTrialSuffix',
    'disableOpenUpgradePage','disableRewardCenter',
    # Quota/trial errors (all first-party)
    'error.proUpgrade','error.openAIFreeLimit','error.proTokenInvalid',
    'error.subscriptionExpired','error.subscriptionExpiredTitle',
    'error.maxQuotaError','error.maxQuotaUsageTips','error.usageTips',
    'error.serveProUnavailable',
}

# Prefix keys (startswith)
PREFIXES = (
    'rewardCenter.',
    'subscription.',
    'currentPlanDescriptionFor',
    'currentYearlyPlanDescription',
    'proQuotaError.',
    'mangaQuotaError.',
)

# Substring matches on the key itself
SUBSTRS = (
    'upgradeToPro','upgradePro','openPro','upgradeMax',
)

def should_blank(k: str) -> bool:
    if k in EXACT:
        return True
    if any(k.startswith(p) for p in PREFIXES):
        return True
    # Substring match: only when key is clearly about pro/upgrade, not about user's own prompt
    low = k.lower()
    for s in SUBSTRS:
        if s.lower() in low:
            return True
    return False

def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        data = json.load(f)
    all_keys = set()
    for lang in data.values():
        if isinstance(lang, dict):
            all_keys.update(lang.keys())
    target = sorted(k for k in all_keys if should_blank(k))
    print(f'Blanking {len(target)} i18n keys across {len(data)} languages.')
    for k in target:
        print(' ', k)
    for lang, bundle in data.items():
        if not isinstance(bundle, dict):
            continue
        for k in target:
            if k in bundle:
                bundle[k] = ''
    with open(SRC, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',',':'))
    print('done')

if __name__ == '__main__':
    main()
