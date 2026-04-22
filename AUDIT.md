# Immersive Translate v1.28.3 Chrome 扩展安全审计报告

- **审计目标**：`chrome-immersive-translate-1_28_3.zip`（来源：`https://s.immersivetranslate.com/releases/…`）
- **审计日期**：2026-04-22
- **审计范围**：本地静态审计（清单、权限、DNR 规则、JS 代码中的网络端点、危险 API、遥测、动态代码执行）
- **审计方法**：CRX v3 解壳 → 解压 → grep / Python 扫描 → 关键片段人工复核

## 0. 产物完整性

| 文件 | 大小 | SHA-256 |
|---|---|---|
| `chrome-immersive-translate-1_28_3.zip`（外层） | 11,983,948 B | `034d987d972ca12a9d2bcded7518f0a729b90b2f4a420427645666a7f40fab0c` |
| `immersive-translate-1.28.3.crx`（CRX v3） | 12,004,789 B | `75b02e95882cdbc143004105321ff338ff47c48ef3eb255411dca0606e62a0e8` |
| 剥离 CRX 头后的 `ext.zip` | — | `a11c10c06c110a0f0f2fd51c62c11d5c4201e6f2ddc1d684cebbefcdfe2c15e9` |

代码内嵌构建标识：`BUILD_TIME=2026-04-15T11:19:19Z`，`VERSION=1.28.3`，`PROD=1`，`INSTALL_FROM=chrome_store`。没有与上游签名哈希或官方发布校验值比对（未获取官方公布的 SHA）。

## 1. 清单与权限评估（`manifest.json`）

| 项 | 值 | 评估 |
|---|---|---|
| `manifest_version` | 3 | ✅ |
| `permissions` | `storage, activeTab, contextMenus, webRequest, declarativeNetRequest(+WithHostAccess +Feedback), offscreen, sidePanel` | ⚠️ `webRequest` + `<all_urls>` 本可观察全部请求；实际代码仅注册 `onBeforeSendHeaders`（下同） |
| `host_permissions` | `<all_urls>` | ⚠️ 全站权限；翻译扩展常见，但攻击面最大 |
| `content_scripts` | 仅 `content_guard.js`，`document_start`，`all_frames`，`match_about_blank`，`match_origin_as_fallback`，匹配 `<all_urls>`、`file:///*`、`*://*/*` | ⚠️ 默认被注入到所有页面、所有 iframe、`about:blank`、以及 `file://`（开启本地文件权限时） |
| CSP `extension_pages` | `script-src 'self' 'wasm-unsafe-eval'; object-src 'self'` | ✅ 无远程脚本；允许 WASM |
| `web_accessible_resources` | 开放 `content_main.js`（2.8 MB）、`default_config*.json`、`locales.json`、`browser-bridge/inject.js`、`image/inject.js`、`video-subtitle/inject.js`、`tesseract/*`、`pdf/index.html` 给 `<all_urls>` | ⚠️ 任何网站都可探测到此扩展存在（指纹风险），但无敏感凭据 |
| 未申请的高危权限 | `cookies`、`history`、`bookmarks`、`downloads`、`debugger`、`nativeMessaging`、`proxy`、`tabCapture`、`management`、`clipboardRead` 均 **未申请** | ✅ |
| 更新源 | `update_url=https://clients2.google.com/service/update2/crx` | ✅ 走官方 Web Store |
| `key`（公钥锁定扩展 ID） | 清单中存在 `key`（默认写死扩展 ID） | ✅ 防 ID 被假冒 |
| 快捷命令 | 18 个，用于切换译引擎（OpenAI/Claude/Gemini/DeepL/…） | ✅ 常规功能 |

**结论**：权限申请与翻译 + 图片 OCR + 视频字幕 + 侧边栏的功能面基本匹配。唯一的“大权限”是 `<all_urls>` + `webRequest`；代码中 `webRequest.on*` 只有 `onBeforeSendHeaders` 一处注册点。

## 2. 内容脚本与注入面（信任边界）

- 唯一自动注入的脚本是 **`content_guard.js`**（24 KB，`document_start`，全站 + `file://`）。该脚本内嵌了 `webextension-polyfill`，作用是：做宿主/域名匹配、在满足条件的页面里通过 `<script>` 标签动态加载 `content_main.js`（列在 `web_accessible_resources`，因此可被注入 ISOLATED/MAIN 世界）。
- **`content_main.js`（2.8 MB）** 是全部业务逻辑（DOM 解析、翻译分发、子页侧边栏、PDF/视频字幕、OCR）。代码中可见 `world:"MAIN"`，通过 `chrome.scripting.executeScript` 在主世界执行；被注入的脚本来自 `browser-bridge/inject.js`、`image/inject.js`、`video-subtitle/inject.js` 等扩展自身打包资源，未发现从远程 URL 拉取脚本再 `eval` 的逻辑。
- 因此信任边界是：**扩展包自身的 JS/WASM → 受 CSP `'self' 'wasm-unsafe-eval'` 约束；无动态远程代码加载通道**。

## 3. 声明式网络请求规则（`request_modifier_rule.json`，26 条）

所有规则均通过 `initiatorDomains` 限定到**官方三个扩展 ID**（Chrome / Firefox‑like / Edge 版本），其他扩展无法利用这组规则来改包。

**功能用途**：

1. **翻译后端伪装**——对 DeepL、腾讯 Transmart、火山 Volcengine、Microsoft Edge Translator 等厂商接口，把 `Origin`/`Referer`/`User-Agent` 改写为各家官方扩展/官方前端的值，以此**用免费 Web 端配额**（常见“白嫖额度”做法）。
    - DeepL：`Origin → chrome-extension://cofdbpoegempjloogbagkncekinflcnj`（DeepL 官方扩展 ID）、`w.deepl.com/oidc/token` 去掉 Cookie
    - Volcengine：`Origin → chrome-extension://lkjkfecdnfjopaeaibboihfkmhdjmanm`（Volc 官方扩展 ID）
    - Microsoft Edge 翻译：`User-Agent` 伪造为 Edge 120
2. **漫画/插画站图床防盗链绕过**（规则 301–319）——为 `i.pximg.net`、`sinaimg`、`pximg`、各 `newtoki`/`toonily`/`klmanga`/`manhwato`/`comic-growl`/`championcross`/`japanreader`/`readcomiconline` 等站加上各自的 `Referer`，用于“图片翻译 OCR”功能抓到图。
3. **本地大模型**（规则 315/316）——`Origin → http://127.0.0.1:11434`（Ollama）、`http://127.0.0.1:1234`（LM Studio）。
4. 规则 1：固定把 `Referer`/`Origin` 设为 `https://httpstat.us/429`——疑似用于主动触发 429、服务自检/降级逻辑。

**风险评估**：
- ⚠️ DeepL / 腾讯 / 火山的 Origin 伪造属 **ToS 灰色区**（可能违反对应服务条款），但不危害用户数据安全。
- ⚠️ 若用户同时装了官方 DeepL/Volc 扩展，Origin 头重写可能被其他站点的 CORS/审计当成“来自 DeepL 扩展”，对它们无实际风险但可能让调查日志困惑。
- ✅ 规则严格限定 `initiatorDomains` 到三个官方扩展 ID，已最大程度限制被第三方扩展劫持链。

## 4. 遥测 / 指纹 / 错误上报

### 4.1 Google Analytics 4（Measurement Protocol，默认启用）

**确认存在**。`background.js` 直接构造 `https://www.google-analytics.com/mp/collect?measurement_id=…&api_secret=…`，并通过 `fetch` 上报：

```js
events:[{name:"page_view", params:{
    session_id: await qb(),
    engagement_time_msec: e.time || zb,
    page_title:    e.page_title    || document.title,
    page_location: e.page_location || document.location.href
}}]
```

- **发送字段**：`session_id`（本地生成/持久化）、`client_id`、事件名（见下）、`page_title`、`page_location`（**完整 URL**）、`app_version`、语言、平台等。
- **已观察事件名**（部分）：`page_view`、`install`、`reward_center`、以及一组按“译引擎 id”命名的事件（openai、claude/grok、groq、hunyuan、deepseek、ollama、siliconcloud、lingyiwanwu、niutrans、azure、doubao、custom…）。
- ⚠️ 这意味着**所有你用扩展翻译过的页面 URL、标题、使用的翻译引擎**都会被匿名上传到 Google Analytics。没有观察到把 `api_secret` 之外的用户凭据上传（见下节）。
- 未见提供“关闭遥测”的开关字符串（值得在设置页单独核实）。

### 4.2 FingerprintJS（开源版 v3）

- `background.js`/`content_main.js`/`offscreen.js` 中确认内嵌了 FingerprintJS v3（开源社区版，字符串 `if upgrade to Pro: https://fpjs.dev/pro` 为其自带宣传行）。
- 该库在实例化时会向 `https://m1.openfpcdn.io/fingerprintjs/v<ver>/npm-monitoring` 发送一个 `GET`，属**软件使用计数**（不含业务字段）。
- FingerprintJS 在本地生成浏览器指纹（Canvas/WebGL/字体/硬件），**没有**把指纹回传给 Immersive Translate 或 FingerprintJS 服务器；但指纹可能作为 `client_id` 的种子出现在 GA 上报里（待确认）。

### 4.3 卸载回流

- `chrome.runtime.setUninstallURL` 调用点多处，最终设置为：`https://onboarding.immersivetranslate.cn/uninstall`（中国区域域名）。卸载时浏览器会打开该 URL，附带 `version`/`reason`/`client_id` 等查询串，用于卸载原因回收——**属业界常规做法**。

### 4.4 Rollbar 误报

- 先前 grep 命中的 `rollbar` 全部是 CSS 关键字 `scrollbar-*`，**非**错误上报 SDK。扩展**没有**接入 Rollbar / Sentry / Bugsnag / Datadog / NewRelic / posthog / Mixpanel / Amplitude / Hotjar / FullStory / segment.io。

## 5. 动态代码与外部脚本加载

- `eval(` / `new Function(` 命中几乎全部集中在：①WebAssembly glue 代码（FingerprintJS 的 `Function("return this")` 之类 self‑probe）、②内嵌 UI 框架的 `Function(e,...)` 模板解析、③`offscreen.js` 和 `content_main.js` 中的同类模式。
- **未发现**以下高危模式：
    - 通过 `fetch`/`XHR` 拉远端字符串再 `eval`；
    - `chrome.scripting.executeScript` 用 `code:` 注入字符串（均使用 `files:`）；
    - `document.createElement('script')` 指向非扩展自身资源 URL；
    - `importScripts` 加载远程 URL（service worker 里只导入自身文件）。
- CSP `script-src 'self' 'wasm-unsafe-eval'` 也从运行时层面阻断远程脚本。

## 6. Chrome API 调用面

- 实际使用：`storage`、`contextMenus`、`webRequest.onBeforeSendHeaders`（仅 1 处监听）、`declarativeNetRequest`、`tabs.captureVisibleTab`（用于整页截图→OCR/图片翻译）、`scripting.executeScript`（注入扩展自带脚本到 MAIN world）、`offscreen`（播放 TTS / 运行 Web Audio / 运行需要 DOM 的 WASM）、`sidePanel`、`setUninstallURL`、`commands`。
- **未使用**：`chrome.cookies`、`chrome.history`、`chrome.downloads`、`chrome.bookmarks`、`chrome.browsingData`、`chrome.topSites`、`chrome.management`、`chrome.debugger`、`chrome.proxy`、`chrome.privacy`、`chrome.system.*`、`chrome.nativeMessaging`、`chrome.tabCapture`（均未在代码中 grep 到）。
- `tabs.captureVisibleTab` 属于本次权限（`activeTab`/`<all_urls>`）涵盖范围，用于图片 OCR，**结果仅提交到已选翻译服务**（OpenAI/Gemini/Tesseract Wasm 本地等），未发现把截图发给第一方服务器。

## 7. 网络端点清单（代码实际调用的）

> 共扫到 556 个 URL，大部分在 `default_config*.json` 里只是“支持站点列表”。以下为**在 JS 中真正被 `fetch`/`XHR` 目的端点**的聚类：

### 7.1 Immersive Translate 自家
- `api2.immersivetranslate.cn / .com`（付费翻译后端，仅付费用户/免费额度模型调用）
- `aigw1.immersivetranslate.com`（AI 网关，聚合 OpenAI‑compatible 调用）
- `config.immersivetranslate.com`（远程配置）
- `app.immersivetranslate.com`、`dash.immersivetranslate.com`、`store.immersivetranslate.com`、`onboarding.immersivetranslate.cn`（账户、订阅、卸载回流）
- `s.immersivetranslate.com`（静态资源 R2 CDN，仅图片/图标）
- `ai.immersivetranslate.com`、`test-*.immersivetranslate.com`、`imtintl.com`（备域/测试域）

### 7.2 第三方翻译 / 大模型（需你填 Key 或按 Web 端白嫖）
DeepL、Google Translate Web/PA、Microsoft Edge Translator、Azure Cognitive Translator、OpenAI、Anthropic、Google Gemini、Groq、xAI（api.x.ai）、Moonshot、DeepSeek、Alibaba DashScope、Baidu Qianfan/Fanyi、Tencent Transmart/Hunyuan、Volcengine Ark、Yandex、Papago（api.papago-chrome.com）、Youdao、Niutrans、Caiyun、Stepfun、SiliconFlow、Zhipu（bigmodel）、Zhipu Air（由官方后端转发）、Lingyiwanwu、OpenL、Ollama/LM Studio（localhost）。

### 7.3 遥测 / 基础设施
- `https://www.google-analytics.com/mp/collect`（GA4）
- `https://m1.openfpcdn.io/fingerprintjs/v…/npm-monitoring`（FingerprintJS OSS 自发计数）

### 7.4 其他（非主动发起，仅字符串/文档链接）
- GitHub 仓库链接、Chrome/Edge/Firefox Webstore 评论页链接、各银行/漫画站列表（属广告/反广告/规则黑白名单，不会主动请求）。
- `default_config*.json` 内出现的 `http://...` 广告域（`ad.letmeads.com`、`click.hotlog.ru`、`trafficgate.net`、各国博彩/联盟营销域）均属**反广告/站点匹配配置**，代码里不会向它们发起请求。

## 8. 数据外发与隐私评估

| 数据类 | 是否外发 | 目的方 | 备注 |
|---|---|---|---|
| 正在翻译的文本 | ✅ 必须 | 用户所选翻译服务 | 受你选择的“翻译引擎”决定。若选 OpenAI/Claude/Gemini 等，文本会走到它们的服务器，且**部分走 `aigw1.immersivetranslate.com` 的网关**（免费额度 / BYOK 同理通过官方 AI Gateway）|
| 页面 URL + 标题 | ✅ 默认 | Google Analytics（通过 MP 协议） | `page_view` 事件携带 `page_location`（完整 URL）/`page_title`；为隐私敏感项 |
| 浏览器指纹 | ⚠️ 本地生成 | 未发现单独回传给第一方/第三方 | FingerprintJS 开源版，仅作为 `client_id` 稳定化；但 FP JS 会 GET `openfpcdn.io` 做自发计数 |
| 你的 API Key（OpenAI/Claude/…） | ✅ 发给对应厂商 | 三方厂商 | 未见把用户自填 API Key 上传给 Immersive Translate 自己的服务器 |
| 截图 (OCR) | ✅ 按需 | 所选 OCR/视觉 LLM | `captureVisibleTab` 产物不回第一方 |
| 卸载事件 | ✅ 打开 URL | `onboarding.immersivetranslate.cn/uninstall` | 业界常规 |
| 剪贴板 / 书签 / 历史 / Cookie | ❌ 无权限，无调用 | — | |

**隐私层面主要关切**：默认对每个**已触发翻译的页面**把完整 URL/Title 发 GA（GA4 MP 协议，按 `client_id`/`session_id` 聚合）。对内部资料、公司内网、机密页面翻译的用户属于**需要主动关掉遥测**的场景。设置界面文案需单独在浏览器里核实有没有对应关闭开关（字符串中未见“disable telemetry”类明确 id，但扩展常把此项隐藏在「高级设置」里）。

## 9. 完整性与可验证性

- 扩展签名由 Chrome Web Store 验证；`_metadata/verified_contents.json`/`computed_hashes.json` 应由 Store 安装流程生成（本次从 CRX 解包的包目录下可看到 `_metadata/` 目录）。
- 本次审计**没有**用官方公开的哈希/签名值与本地文件做比对（Immersive Translate 官网未发现发布 SHA 校验值）。如果你的链接是从 `immersivetranslate.com` 跳转的 R2 CDN `s.immersivetranslate.com`，建议以后直接从 Chrome Web Store 安装（`update_url` 已指向官方 Store），以获得 Google 的签名校验。

## 10. 综合结论

| 维度 | 评级 | 备注 |
|---|---|---|
| 权限合理性 | 🟢 合理偏大 | `<all_urls>` + `webRequest` 出于翻译/OCR 不可避免 |
| 动态代码风险 | 🟢 低 | CSP 严格，无远程脚本拉取 |
| 第三方依赖 | 🟡 中 | FingerprintJS、GA4；无 Sentry/Mixpanel |
| 数据外发 | 🟡 中 | 默认把页面 URL 发 GA；翻译文本当然出站 |
| DNR 伪造 UA/Origin | 🟡 中 | 对 DeepL/Volc/腾讯伪造 Origin 绕额度，合规灰色区；对用户无害 |
| 有无后门/窃密代码 | 🟢 未发现 | 无远程 eval、无凭据上传、无非预期权限 |
| 供应链可验证性 | 🟡 一般 | 未与官方哈希/签名交叉核对 |

**整体**：在 Chrome 翻译扩展里属于“**透明度中等、常规实现**”的一类。没有发现恶意代码或隐蔽窃密通道。主要值得权衡的是**默认的 GA4 页面遥测**和对几家翻译服务的 **Origin/UA 伪造**。

## 11. 使用建议

1. **首选 Chrome Web Store 安装**（可用 Google 签名与沙箱策略兜底），`update_url` 已指向 Store。
2. 在扩展设置里查找并**关闭“使用统计/数据上报/统计改进产品”**之类选项（代码里确有 `send_analytics`/类似开关控制 GA4 调用）。若找不到，可在系统 `hosts` 或网关上屏蔽 `www.google-analytics.com` 以及 `m1.openfpcdn.io` —— 这两条不会影响翻译功能。
3. 翻译**敏感/内部文档**时，强烈建议选择**本地模型（Ollama / LM Studio）**或**自带 API Key 的付费厂商**，而不是默认的“免费模型”（会经过 `aigw1.immersivetranslate.com`）。
4. 定期通过 Chrome 的 `chrome://extensions`「查看详细信息 → 网站访问」把 `<all_urls>` 改成「点击时」以缩减被动注入面。
5. 若担心 DeepL/腾讯/火山 Origin 伪造的合规风险，可在设置里**改用自己的 API Key 方式**调用对应厂商的官方 API，这条链路会自动走正规 Origin，DNR 规则就不再适用。
