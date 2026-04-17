# Fast Video Download ⚡️

一个轻量、高效的全能视频下载工具。基于强大的 `yt-dlp` 引擎，支持超过 1800+ 网站的解析与下载。

## ✨ 核心特性

- **极致覆盖**：无缝支持 YouTube、Bilibili、TikTok、Twitter/X 等全球 1800+ 视频流媒体平台。
- **免密突破**：内置抖音等特供策略，无需配置 Cookie 即可提取最高画质无水印视频。
- **暗夜极客风 UI**：使用纯 CSS 与 Vue 3 打造的高颜值毛玻璃+紫粉渐变视觉体验。
- **防盗链优化**：自带后端图片代理转发服务，轻松解决跨域及图片渲染防盗链问题。
- **去繁就简**：没有支付墙、无需登录、没有冗余的数据库依赖，粘贴链接即可下载。

## 🛠 技术栈

- **前端**: Vue 3 + Vite + Vanilla CSS
- **后端**: FastAPI (Python) + Uvicorn
- **核心引擎**: yt-dlp 

## 🚀 快速启动

你需要分别启动前端与后端服务。

### 1. 启动后端 (Backend)

进入 `backend` 目录，安装依赖并启动 FastAPI 接口：

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
*(后端运行后默认运行在 http://127.0.0.1:8000)*

### 2. 启动前端 (Frontend)

进入 `frontend` 目录，安装 Node 依赖并启动 Vite：

```bash
cd frontend
npm install
npm run dev
```

打开浏览器访问终端打印的本地地址（通常是 `http://localhost:5173`），即可开始体验你的全能视频下载器！

## ⚖️ 免责声明与版权 (Compliance & Disclaimer)

**本项目仅用于技术学习和研究目的 (For technical learning and research purposes only)。**

1. **合法授权**：请用户仅下载自己拥有版权或已获得合法授权的内容。
2. **遵守法规**：用户应自行遵守所在地区的法律法规。
3. **平台条款**：用户应遵守各视频/音频平台的服务条款。
4. **风险自担**：使用即表示您同意自行承担所有可能造成的法律后果。开发者不对任何形式的滥用行为负责。

---
© 2024 Fast Video Download. All Rights Reserved. 保留所有权利。
