# 扬旗而行 · 公众号编辑部

> AI 驱动的公众号写作工具，支持 DeepSeek + 智谱 GLM，自动生成爆款标题、摘要、封面提示词。

## 功能特点

- ✍️ **AI 写稿**：输入草稿，AI 润色为公众号风格爆款文章
- 🏷️ **标题推荐**：3 个候选标题，点击即选
- 📝 **首屏摘要**：50-100 字摘要，提升打开率
- 🎨 **封面提示词**：AI 生成 3 套封面构图提示词
- ✅ **合规审查**：自动检查敏感词/政治风险
- 📱 **响应式界面**：单栏精致卡片，随时随地写作

## 使用方式

1. 直接用浏览器打开 `yangqi-editor.html`
2. 点右上角 ⚙️ 配置 DeepSeek API Key 和智谱 API Key
3. 开始写作

## 技术栈

- 纯前端 HTML（Tailwind CDN，无需构建）
- DeepSeek API（写作引擎）
- 智谱 GLM-4-Flash（合规审查）
- 智谱 CogView-4（封面图生成）

## 注意事项

- API Key 存在浏览器 localStorage，不会上传到 GitHub
- 封面图代理需要本地运行 `cover-proxy.py`
- 公众号发布代理需要本地运行 `publish-proxy.py`
