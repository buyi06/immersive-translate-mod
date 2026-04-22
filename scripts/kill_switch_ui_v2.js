/* IMT-MOD UI kill-switch v2 — hide paid/login/reward/sync/donate/report nodes by class & textContent */
(function(){
  if (typeof document === 'undefined') return;
  if (window.__IMT_MOD_UI_V2__) return;
  window.__IMT_MOD_UI_V2__ = true;

  // ------- 1. CSS-based hard hide (attribute & class patterns) -------
  var CSS = [
    '[class*="paywall" i]','[class*="Paywall"]','[id*="paywall" i]',
    '[class*="subscription" i]','[class*="Subscription"]',
    '[class*="upgrade" i]','[class*="Upgrade"]','[class*="-upgrade"]',
    '[class*="pricing" i]','[class*="Pricing"]',
    '[class*="reward-center" i]','[class*="RewardCenter"]','[class*="rewardCenter" i]',
    '[class*="pro-badge" i]','[class*="ProBadge"]',
    '[class*="vip" i]','[class*="VIP"]','[class*="Vip"]',
    '[class*="premium" i]','[class*="Premium"]',
    '[class*="buy-pro" i]','[class*="BuyPro"]',
    '[class*="login" i]','[class*="Login"]','[class*="signin" i]','[class*="SignIn"]',
    '[class*="sync-to-account" i]','[class*="syncToAccount" i]','[class*="SyncAccount"]',
    '[class*="user-menu" i]','[class*="UserMenu"]','[class*="account-menu" i]','[class*="AccountMenu"]',
    '[class*="avatar" i][class*="user" i]','[class*="UserAvatar"]',
    '[class*="feedback" i]','[class*="Feedback"]',
    '[class*="donate" i]','[class*="Donate"]','[class*="coffee" i]',
    '[class*="referral" i]','[class*="Referral"]','[class*="invite" i]','[class*="Invite"]',
    '[class*="wechat" i][class*="community" i]','[class*="QrCode"][class*="WeChat" i]',
    '[data-testid*="paywall" i]','[data-testid*="subscription" i]',
    '[data-testid*="upgrade" i]','[data-testid*="reward" i]',
    '[data-testid*="login" i]','[data-testid*="account" i]','[data-testid*="premium" i]',
    '[href*="pricing" i]','[href*="subscribe" i]','[href*="upgrade" i]',
    '[href*="reward" i]','[href*="/login" i]','[href*="/signin" i]',
    '[href*="donate" i]','[href*="coffee" i]','[href*="referral" i]','[href*="invite" i]',
    '[href*="immersivetranslate.com" i]','[href*="immersivetranslate.cn" i]',
    '[href*="imtintl.com" i]','[href*="buymeacoffee" i]'
  ].join(',');
  var css = CSS + '{display:none!important;visibility:hidden!important;pointer-events:none!important;height:0!important;width:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important}';
  function inject(){
    if (!document.head) return;
    var id = 'imt-mod-ui-hide-v2';
    if (document.getElementById(id)) return;
    var s = document.createElement('style');
    s.id = id; s.textContent = css;
    document.head.appendChild(s);
  }
  inject();
  new MutationObserver(function(){
    if (!document.getElementById('imt-mod-ui-hide-v2')) inject();
  }).observe(document.documentElement, {childList:true, subtree:true});

  // ------- 2. Text-based hiding -------
  // Banned substrings that appear on banned UI nodes (multi-lingual).
  // All lowercase; matched case-insensitively.
  var PHRASES = [
    // Login / account (avoid matching prompt 'log in' - too generic? use context words)
    '登录后可开通会员','立即登录','去登录','未登录','已登录','登录 / 注册','登录/注册',
    '退出登录','退出账号','注销账号','注销登录',
    '管理账户','我的账号','账号中心','个人中心','帐号中心','帐户中心',
    // Pro/VIP/premium
    'pro 会员','pro会员','pro 版','pro版','高级会员','高级版','专业版',
    'vip 会员','vip会员','付费会员','开通会员','续费会员','年度会员','月度会员',
    '免费试用 pro','免费试用pro','免费体验 pro','免费体验pro',
    '升级到 pro','升级到pro','升级pro','升级到高级版','升级会员',
    '升级 max','升级max','max 会员','max会员',
    'free plan','free trial','upgrade to pro','upgrade pro','upgrade to max',
    'pro plan','pro membership','pro subscription','premium','subscribe',
    'manage account','log in','sign in','sign up','sign out','log out',
    // Reward center
    '奖励中心','领取奖励','奖励任务','积分中心','兑换奖励','奖励 pdf','奖励 视频',
    'reward center','claim reward','reward task','redeem',
    // Sync / cloud
    '同步到沉浸式翻译','同步到云端','同步到账号','云同步','同步配置',
    'sync to account','sync to cloud',
    // Donate / feedback / community
    '赞助','打赏','捐赠','请作者喝','请我喝','buy me a coffee','donate',
    '意见反馈','提交反馈','反馈建议','加入社群','加入用户群','加入我们','官方社群',
    '微信公众号','关注公众号','加微信','客服微信','微信社群',
    'feedback','join community',
    // Invite / referral
    '邀请好友','推荐给朋友','推广链接','邀请码','兑换码','cd-key','cdkey','redeem code',
    'invite friend','refer a friend','promo code',
    // Quota / pay errors
    '配额已用完','额度已用完','免费额度','付费额度','试用额度','会员权益',
    'quota exceeded','subscription expired','trial ended',
    // Price / plan labels
    '价格方案','查看套餐','购买套餐','订阅套餐','支付宝','微信支付','stripe',
    'pricing','checkout','billing',
    // Homepage link
    '官网','官方网站','项目主页','homepage','official site'
  ];

  function normalize(s){
    return (s || '').replace(/\s+/g,' ').trim().toLowerCase();
  }

  function matches(text){
    if (!text) return false;
    var t = normalize(text);
    if (t.length > 200) return false; // long blocks → skip
    for (var i=0;i<PHRASES.length;i++){
      if (t.indexOf(PHRASES[i]) !== -1) return true;
    }
    return false;
  }

  // Heuristic: climb up to the closest "navigation/button/card" ancestor.
  // Patterns: nav item, menu item, link, button, list-item, card, tile.
  var CONTAINER_SEL = [
    'a','button','li',
    '[role="button"]','[role="menuitem"]','[role="link"]','[role="tab"]','[role="option"]',
    '.menu-item','.nav-item','.nav-link','.sidebar-item','.sidebar-link',
    '.ant-menu-item','.ant-menu-submenu-title','.ant-btn','.ant-card','.ant-list-item',
    '.el-menu-item','.el-submenu__title','.el-button','.el-card',
    '.settings-item','.setting-item','.option-item','.card','.tile',
    '[class*="MenuItem"]','[class*="NavItem"]','[class*="SidebarItem"]',
    '[class*="menu__item"]','[class*="nav__item"]','[class*="sidebar__item"]',
    '[class*="ListItem"]','[class*="list-item"]'
  ].join(',');

  function findContainer(node){
    var n = node;
    var steps = 0;
    while (n && n.nodeType === 1 && steps < 8){
      if (n.matches && n.matches(CONTAINER_SEL)) return n;
      n = n.parentElement;
      steps++;
    }
    // Fallback: the original node itself if it is a block-ish element.
    return node.nodeType === 1 ? node : node.parentElement;
  }

  function hide(el){
    if (!el || el.__imtModHidden) return;
    try {
      el.__imtModHidden = true;
      el.setAttribute('data-imt-mod-hidden','1');
      el.style.setProperty('display','none','important');
      el.style.setProperty('visibility','hidden','important');
      el.style.setProperty('pointer-events','none','important');
    } catch(_){}
  }

  function scanRoot(root){
    try {
      if (!root || !root.querySelectorAll) return;
      // Walk only visible-ish text nodes' parents to limit cost.
      var candidates = root.querySelectorAll('a,button,li,span,div,p,h1,h2,h3,h4,h5,[role]');
      for (var i=0;i<candidates.length;i++){
        var el = candidates[i];
        if (el.__imtModChecked) continue;
        el.__imtModChecked = true;
        // Skip inputs & textareas (we don't want to hide the user's own AI-API config fields)
        var tag = el.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') continue;
        // Skip if inside form of custom AI API (safety)
        if (el.closest && el.closest('[data-imt-keep], form[class*="openai" i], form[class*="custom" i]')) continue;
        // Quick filter: only check leaf-ish nodes to avoid hiding the whole page
        if (el.children && el.children.length > 12) continue;
        var text = el.textContent;
        if (!text || text.length > 160) continue;
        if (matches(text)){
          hide(findContainer(el));
        }
      }
    } catch(_){}
  }

  function scanAll(){
    scanRoot(document.body);
    // Also scan any open shadow roots we can reach.
    try {
      var all = document.querySelectorAll('*');
      for (var i=0;i<all.length;i++){
        if (all[i].shadowRoot) scanRoot(all[i].shadowRoot);
      }
    } catch(_){}
  }

  var scheduled = false;
  function schedule(){
    if (scheduled) return;
    scheduled = true;
    (window.requestIdleCallback || function(cb){ setTimeout(cb, 50); })(function(){
      scheduled = false;
      scanAll();
    });
  }

  function boot(){
    scanAll();
    new MutationObserver(function(muts){
      // Clear cached flag on changed subtrees so new content is re-evaluated.
      for (var i=0;i<muts.length;i++){
        var m = muts[i];
        if (m.type === 'childList'){
          m.addedNodes && m.addedNodes.forEach(function(n){
            if (n.nodeType === 1){
              n.__imtModChecked = false;
              try { n.querySelectorAll && n.querySelectorAll('*').forEach(function(c){ c.__imtModChecked = false; }); } catch(_){}
            }
          });
        } else if (m.type === 'characterData' && m.target && m.target.parentElement){
          m.target.parentElement.__imtModChecked = false;
        }
      }
      schedule();
    }).observe(document.documentElement, {childList:true, subtree:true, characterData:true});
    // Periodic backstop
    setInterval(schedule, 2000);
  }

  if (document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', boot, {once:true});
  } else {
    boot();
  }
})();
