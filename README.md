# Immersive Translate 1.28.3 · 自用精简版

基于 **Immersive Translate 官方 Chrome 扩展 v1.28.3**（Web Store 版）做的私人审计与修改版本。

> ⚠️ **仅供个人学习与离线使用**。原作品版权归 [immersivetranslate.com](https://immersivetranslate.com/) 所有。本仓库**不接受分发诉求**、**不建议装在非研究环境**、**和原作者与官方均无关联**。

---

## 这个版本改了什么

四个方向的定制（细节见 [`CHANGELOG.md`](./CHANGELOG.md)，审计依据见 [`AUDIT.md`](./AUDIT.md)）：

1. **彻底关闭遥测与数据上传** — Google Analytics / GTM / FingerprintJS / weixin 子域全部断网（fetch / XHR / sendBeacon 三层拦截）；`setUninstallURL` 被 stub。
2. **移除付费 / VIP / 会员相关逻辑与界面** — i18n 里 132 个 key × 19 种语言被清空；登录 / 订阅 / 奖励中心 / 升级入口在 Options / Popup / Side-panel 的 DOM 不再出现。
3. **切断与一方服务器通信 + 解锁 Pro 功能** — 对 `immersivetranslate.com / .cn / imtintl.com / immersive-translate.owenyoung.com / immersive-translate.deno.dev` 的所有请求返回伪造的"终身 Max"用户 JSON；`chrome.storage.get` 对读取结果做深度改造，把 `isPro/isMax/isVip/plan/level/subscription.active` 等字段强制置为真；AI 字幕 / BabelDoc PDF / 漫画翻译 / 视频字幕 / 写作助手等功能在 UI 层解锁。
4. **删除官方付费 / 免费模型服务条目** — `translationServices` 里剔除了 10 条一方 IMT-hosted 服务（DeepL Pro 官方 / GLM-4.7 Pro / GLM-4.5 Air Pro / GLM-4 Flash 官方免费 / Babel Lite 免费 / Pro 模板基底 / 等）；在下拉 / 列表 / 弹窗里这些条目均不可见。

### 保持原样

- **自定义 AI API**：OpenAI / Gemini / Claude / DeepSeek / OpenRouter / Ollama / Groq / SiliconCloud / 豆包 / 通义 / 智谱 BYOK / Kimi / 混元 / Azure OpenAI / Lingyiwanwu / Grok 等**全部保留**（用户自己填 API Key 的服务，流量不经过 IMT 一方域）。
- **公共免费通道**：Google 翻译 / Bing / 百度 / 腾讯 / Caiyun / 有道 / Yandex 等直连公共端点的引擎**全部保留**。
- **本地端点**：`localhost / 127.0.0.1 / 0.0.0.0` 被显式放行，本地 Ollama / LM Studio 不受影响。

---

## 安装

> **最省事**：用下面"方式三"直接下载打包好的 zip；想跟进 commit 就用方式一（clone）。

### 方式三：直接下载预构建 zip（推荐，适合只想用不想折腾的人）

仓库根目录已经放了一份**打包好的、manifest.json 在 zip 根**的压缩包：

- 直链：<https://github.com/buyi06/immersive-translate-mod/raw/main/immersive-translate-mod-v3.zip>
- 或在 GitHub 页面上点 `immersive-translate-mod-v3.zip` → `Download raw file`

1. 下载 `immersive-translate-mod-v3.zip` 到本地（**不要**用 `s.immersivetranslate.com/releases/chrome-immersive-translate-1_28_3.zip` — 那是原版未修改）。
2. 解压到一个稳定目录（文件夹里直接能看到 `manifest.json` 就对了）。
3. 打开 `chrome://extensions/` → 右上角开"**开发者模式**"。
4. 如果之前装过 Immersive Translate（不管官方版还是旧 Mod），**点"移除"**，再把 Chrome 完全退出后重开。
5. 点"**加载已解压的扩展程序**"，选刚解压出的那个根目录。

**装完 3 秒自检**（打开扩展的 Options 页 → F12 → Console 粘贴）：

```js
document.getElementById('imt-mod-v3-css')?.textContent?.includes('imtintl.com')
// true  → 装对了，Mod 生效
// false / undefined → 装的还是原版或旧 Mod
```

每次我推新修复后这个 zip 也会同步更新；文件名不变，重新下载替换即可。

### 方式一：直接 clone 后加载

```bash
git clone <this-repo-url> immersive-translate-mod
```

1. 打开 Chrome / Edge / Brave → `chrome://extensions/`
2. 右上角打开"**开发者模式**"
3. 点击"**加载已解压的扩展程序**"，选择 clone 下来的仓库根目录
4. 扩展会立刻出现在工具栏

### 方式二：下载 ZIP

1. GitHub 页面右上角 → Code → Download ZIP
2. 解压到一个你不会移动的目录
3. 剩下步骤同上

> 开发者模式加载的是"已解压"文件夹，**不能直接把 .zip 拖进扩展页**，必须先解压。每次 Chrome 启动会有一条"关闭开发者模式扩展"的提示，正常情况可以忽略。

### 首次使用

1. 点扩展图标 → 齿轮图标进入 Options 页
2. 默认翻译引擎是 **Bing**，直接开箱可用
3. 如果想用大模型翻译，Options → 翻译服务 → 添加你自己的 OpenAI / DeepSeek / Claude / 自定义 AI 的 API Key 和 endpoint

> 如果你之前装过官方版本，建议先删掉，再装这个，避免 `chrome.storage` 里残留旧的订阅状态数据产生 UI 混乱（本修改版的 storage 过滤层会清掉绝大多数残留字段，但全新状态更干净）。

---

## 目录结构

```
.
├── manifest.json              # Chrome 扩展清单（已去除 update_url 和 key，防止自动替换回官方版）
├── background.js              # Service Worker，已注入 v2 kill-switch（遥测拦截 + Pro 用户伪造）
├── content_main.js            # 页面内容脚本
├── content_guard.js
├── offscreen.js, offscreen.html
├── options.js, options.html   # 设置页，已额外叠加 UI v2+v3（付费/VIP/一方模型条目隐藏）
├── popup.js, popup.html
├── side-panel.js, side-panel.html
├── default_config.json        # 翻译服务注册表，已删除 10 条一方模型
├── default_config.content.json
├── request_modifier_rule.json # DNR 规则（已删除限流降速规则）
├── locales.json               # 内嵌 i18n，132 key × 19 语言清空
├── _locales/                  # Chrome 原生 i18n
├── icons/, badge-icons/, styles/, image/, pdf/, video-subtitle/, browser-bridge/
├── aifw/                      # 广告过滤器 / reading-rule
├── tesseract/                 # OCR 运行时
├── wasm/                      # PDF / 其他 wasm 模块
├── AUDIT.md                   # 原始审计报告（静态 + 动态审计 + 网络行为 + 威胁建模）
├── CHANGELOG.md               # 本次修改详细变更表
└── scripts/                   # 可复现的 patch 源码（不参与扩展运行）
    ├── kill_switch_core_v2.js    # 在扩展启动时 prepend 到 7 个入口 JS 的核心逻辑
    ├── kill_switch_ui_v2.js      # Options/Popup/Side-panel 上 UI 层隐藏（CSS + MutationObserver）
    ├── kill_switch_ui_v3.js      # 死 ID 精准隐藏（attribute 匹配 + <option> 物理移除 + storage 深度剥离）
    ├── blank_i18n.py             # 清空 locales.json 中 132 key × 19 lang 的脚本
    ├── delete_official_services.py   # 从 default_config*.json 删除一方服务的脚本
    └── test_harness.js           # Node 沙箱测试（88 个断言，全部 PASS）
```

---

## 如何复现这些修改

参见 [`scripts/README.md`](./scripts/README.md)。

快速校验：

```bash
cd scripts
node test_harness.js
# 预期输出：88 passed   0 failed
```

---

## 常见问题

**Q: 为什么图标还显示官方 Logo？**  
A: 本修改版没改视觉资产（icons/、badge-icons/ 原封不动）。如果你想和原版区分，自己替换 `manifest.json` 里 `icons.*` 引用的 png。

**Q: 为什么翻译还是有次数限制？**  
A: 额度限制一般只出现在"官方付费模型"（已从下拉删除），用 BYOK（自己的 API Key）和公共引擎（Bing/Google/百度等）无此限制。

**Q: 官方 Cloud 同步还能用吗？**  
A: 不能。Cloud 同步依赖一方服务器，这里已经断网。本地设置完全由 `chrome.storage.local/sync` 保存（chrome.storage.sync 仍然会跨你登录 Chrome 的设备同步，但不经过 IMT 服务器）。

**Q: 会不会自动更新回官方版？**  
A: 不会。`manifest.json` 已经移除 `update_url` 和 `key`，加载时 Chrome 会重新给它一个随机扩展 ID，不会和官方版冲突，也不会被官方更新覆盖。

**Q: 原版的"奖励中心 / 积分"还在吗？**  
A: 入口在 UI 被隐藏，后端接口返回伪造的 9 × 10¹² 余额。相关逻辑不会主动发请求，所以看起来就像"没有这东西"。

---

## 致谢 / 合规

- 原作品：[Immersive Translate](https://immersivetranslate.com) — 所有版权归原作者。
- 本仓库是**研究性质的本地修改副本**，不含盈利动机、不分发付费密钥、不规避 Chrome Web Store 审核。
- 如官方团队认为本仓库侵权，请开 Issue 或通过 GitHub 官方 DMCA 流程处理，我会尽快下架。
