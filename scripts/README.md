# scripts/ — 可复现修改的源码

这个目录里的代码**不会被扩展运行时加载**，它们纯粹是为了你能看到“怎么从官方原版改成这个版本”。

仓库根目录中 7 个入口 JS 的文件头已经 prepend 好了这里的 3 个 kill_switch，所以安装时不需要再执行他们。

## 文件

| 文件 | 作用 |
|---|---|
| `kill_switch_core_v2.js` | 网络拦截 + Pro 用户伪造；作为 IIFE 被 prepend 到每个入口 bundle 的文件头 |
| `kill_switch_ui_v2.js` | CSS 通用隐藏 + MutationObserver；盖住付费 / 会员 / 奖励 / 订阅类的容器 |
| `kill_switch_ui_v3.js` | 精准按 ID 删除一方服务 `<option>` + storage 读取时把默认引擎回写为 `bing` |
| `blank_i18n.py` | 将 `locales.json` 中 132 个付费/VIP 相关 key × 19 种语言全部清空为空字符串 |
| `delete_official_services.py` | 从 `default_config.json` 和 `default_config.content.json` 的 `translationServices` 中删除 10 个一方服务条目 |
| `test_harness.js` | Node.js 沙箱测试 (88 个断言)，validate 上述所有行为 |

## 复现步骤（若你想从一个新的 v1.28.3 官方解压包重新应用这些修改）

```bash
# 假设你把官方解压包放在 ./ext/。

# 1. 清理 manifest：手动编辑 ext/manifest.json，删除 "update_url" 和 "key"。

# 2. 清空 i18n
python3 scripts/blank_i18n.py ext/locales.json

# 3. 删除一方服务条目
python3 scripts/delete_official_services.py \
  ext/default_config.json \
  ext/default_config.content.json

# 4. 面向 7 个入口 bundle 做 prepend（伪代码，按自己环境改）
for f in background.js content_main.js content_guard.js offscreen.js options.js popup.js side-panel.js; do
  {
    cat scripts/kill_switch_core_v2.js
    cat scripts/kill_switch_ui_v2.js
    cat scripts/kill_switch_ui_v3.js
    cat ext/$f
  } > ext/$f.new && mv ext/$f.new ext/$f
done

# 5. 跑测试
node scripts/test_harness.js   # 预期：88 passed
```

实际在本仓库生成时，对 7 个 bundle 的 v2 core prepend 是通过省略号脚本批量处理的，另外做了“旧 v1 core 从已有 bundle 中 marker-slice 移除 + v2 重新写入”的更换。这里的脚本是我手头这一次执行时的快照，足以重复框架，但如果你要对官方新版本（v1.29, v1.30…）郻用，树结构和类名可能会变，需要根据 `AUDIT.md` 的前置审计修改 selector 和 marker。
