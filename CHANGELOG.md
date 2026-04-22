# CHANGELOG

基线：Immersive Translate v1.28.3 Chrome Web Store 版（原始 zip SHA-256 `034d987d972ca12a9d2bcded7518f0a729b90b2f4a420427645666a7f40fab0c`）。

本仓库打包后的扩展 zip SHA-256：`a1faa5a87b1c669bc00e4d0a604956b257fa1ad9059d7d3ab96451ec1e73a438`。

测试状态：`node scripts/test_harness.js` → **88 / 88 PASS**。

---

## 1. manifest.json 清理

- 删除 `update_url`（防止 Chrome 自动拉官方版替换）
- 删除 `key`（加载后 Chrome 会重新分配随机扩展 ID，和官方版互不干扰）
- 删除 remote-debug 相关 `host_permissions` 中对 IMT 一方域的条目（保留 `<all_urls>`）
- `default_locale` 保留，仅清空付费/VIP/登录相关项，不影响翻译 UI

## 2. default_config.json / default_config.content.json 清理

从 `translationServices` 数组移除以下 10 个一方 IMT-hosted 条目（两份配置同步处理）：

| id | 说明 |
|---|---|
| `dpro` | DeepL Pro 官方代理 |
| `free-model` | 官方"免费模型"模板 |
| `babel-lite-free` | Babel Lite 免费模型 |
| `babel-lite-free.add_v.[1.23.9]` | Babel Lite 免费（新版本标记） |
| `zhipu-pro` | GLM-4.7 Pro 官方 |
| `zhipu-pro.add_v.[1.15.3]` | GLM-4.7 Pro 新版本标记 |
| `zhipu-air-pro` | GLM-4.5 Air Pro 官方 |
| `zhipu-air-pro.add_v.[1.20.12]` | GLM-4.5 Air Pro 新版本标记 |
| `zhipu-base` | GLM-4 Flash Pro 模板基底 |
| `zhipu-free` | GLM-4 Flash 官方免费 |

保留的服务（BYOK 或公共直连）：85 条，覆盖 OpenAI / Gemini / Claude / DeepSeek / OpenRouter / Ollama / Groq / SiliconCloud / 豆包 / 通义 / 智谱 BYOK / Kimi / 混元 / Azure OpenAI / Lingyiwanwu / Grok / Qianfan / Google / Bing / 百度 / 腾讯 / Caiyun / 有道 / Yandex / DeepL BYOK / Transmart 等。

## 3. request_modifier_rule.json

移除官方预设的 DNR 限流 / 缓存降级 rule，保留用于跨域 header 注入的默认规则。

## 4. locales.json (i18n 清空)

执行 `scripts/blank_i18n.py`：

- 132 个 i18n key × 19 种语言（en, zh-CN, zh-TW, zh-HK, ja, ko, fr, de, es, pt-BR, ru, it, ar, hi, id, vi, th, tr, uk）被清空为空字符串
- 涉及类别：登录 / 注册 / 订阅 / 升级 / 会员中心 / 奖励中心 / 积分 / 付费 / VIP / Pro / Max / 费率 / 额度 / 邀请 / 分享赚点数 / 隐私声明中指向付费的条款
- 翻译功能本身的所有文案保留完整

## 5. 注入代码（3 个 IIFE）

7 个入口 JS (`background.js`, `content_main.js`, `content_guard.js`, `offscreen.js`, `options.js`, `popup.js`, `side-panel.js`) 文件头依次 prepend 以下 3 个 IIFE：

### 5.1 `kill_switch_core_v2.js` (10,374 B)

约束：`__IMT_MOD_CORE_V2__` 全局守卫，重复注入时早期返回。

拦截的网络调用：
- `fetch`：包装为可分类器
- `XMLHttpRequest.prototype.open/send/setRequestHeader`：记录 URL 后分类
- `navigator.sendBeacon`：全部 stub 为 no-op 并返回 `true`

分类 `classify(url)`：
- **IMT 一方域**：`immersivetranslate.com`, `immersivetranslate.cn`, `imtintl.com`, `immersive-translate.owenyoung.com`, `immersive-translate.deno.dev`, `imt-mod-null.invalid` → 返回伪造 `envelope(PRO_USER)` JSON。20x。
- **遥测域**：`google-analytics.com`, `analytics.google.com`, `googletagmanager.com`, `openfpcdn.io`, `fpjs.dev`, `api.fpjs.io`, `fingerprintjs.com`, `subhub.weixin.so` → `204 No Content`，空 body。
- **白名单**：`chrome-extension:/moz-extension:/data:/blob:/about:/localhost/127.0.0.1/0.0.0.0` + 相对路径 → 直通。
- **其余**：直通（兼容 BYOK 和公共引擎）。

伪造 PRO 身份（envelope）：
- Boolean：`isPro / isMax / isVip / isPaid / isPremium / isSubscribed / hasPro / hasVip / hasPremium / hasSubscription / pro / vip / premium = true`
- Boolean：`isTrial / trial = false`
- String = `'max'`：`level / plan / planLevel / userLevel / userType / accountType / membershipLevel / subscriptionType`
- 时间戳：`expireAt = expiresAt = expiredAt = renewalDate = 4102444800000`（2100-01-01）
- 余额：`balance = points = credits = 9e12`
- 嵌套：`subscription.{active, plan, level, status, expireAt}`, `features.*`（18 个功能 flag）, `quota.{total, remaining}`, `usage`, `limits`

`chrome.storage.local/sync/session.get` 被包装：回调前遍历结果，对类 `user/subscription/plan/level/isPro/...` 的 key 强制注入伪造值。`.set` 也做一次正向写入（首次安装时产生持久化记录）。

`chrome.runtime.setUninstallURL` 被覆盖为 no-op，干净卸载。

**已知修复** (相比 v1 core)：`jsonResponse(obj, status)` 在 `status ∈ {204, 205, 304}` 或 obj 为空时 body 置 null（符合 HTTP 规范，避免 `new Response('{}', {status: 204})` 抛 `TypeError`）。

### 5.2 `kill_switch_ui_v2.js` (9,877 B)

约束：`__IMT_MOD_UI_V2__` + `<style id="imt-mod-ui-hide-v2">`。

用 CSS 隐藏以下容器：
- `[class*="upgrade"]`, `[class*="pro-badge"]`, `[class*="vip"]`, `[class*="premium"]`, `[class*="reward"]`, `[class*="subscription"]`, `[class*="plan"]`, `[class*="member"]`
- `[data-testid*="upgrade"]` / `[data-testid*="reward"]` / `[data-testid*="login"]`

`MutationObserver` 持续监控 DOM，新入节点命中隐藏规则时即时 `display:none`。

### 5.3 `kill_switch_ui_v3.js` (4,592 B)

约束：`__IMT_MOD_UI_V3__` + `<style id="imt-mod-ui-hide-v3">`。

精准隐藏 `DEAD_IDS`：`dpro`, `free-model`, `babel-lite-free`, `babel-lite`, `zhipu-pro`, `zhipu-air-pro`, `zhipu-base`, `zhipu-free`。

执行两个事情：
1. `<option value="死 ID">` 在 MutationObserver 中被 **物理删除**（`.remove()`，不是隐藏）。
2. `chrome.storage.local/sync.get()` 结果中 `translationService / clientImageTranslationService / inputTranslationService / streamTranslationService` 如果等于死 ID，回调前覆写为 `bing` / `inherit`。

## 6. 测试

`scripts/test_harness.js` 是 Node.js 沙箱（`vm.createContext` 模拟 Chrome 扩展全局）。

11 类 / 88 个断言：
1. 全局 marker（注入 / 重复注入早返）
2. `fetch` + IMT 域 → 200 + 伪造 Pro JSON
3. `fetch` + 遥测域 → 204 null-body  
4. `fetch` + 公共引擎域 → 直通
5. XHR 同样三层分类
6. `navigator.sendBeacon` 返回 true 且无请求
7. `chrome.storage.get` 深度注入 + 读取反验
8. `setUninstallURL` stub
9. 注册表 DELETED 10 条
10. 7 bundle 的 v2 core 完整性
11. manifest 完整性

最新一次运行：`88 passed, 0 failed, exit 0`。

## [mod-1.28.3+3] - 2026-04-22
### Removed
- 使用须知合规弹窗（options.js 中 `wL` 组件存桩，自动 confirm）
### Fixed / Unlocked
- YouTube AI 智能分句 `subtitle.ytAIAsr` 默认可见且可开关（解除 Zt + isPro 闸门）
- “添加自定义翻译服务” Picker 完整呈现 Custom AI / OpenAI / Claude / Gemini / DeepSeek / Groq / SiliconCloud / Ollama（移除 ny 用户级过滤）
