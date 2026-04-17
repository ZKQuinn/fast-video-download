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

## ⚠️ 声明
本项目仅供编程学习交流，请尊重各平台的用户协议，勿将解析内容的下载用于非法盈利。
