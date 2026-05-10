# Agents Guide

本文件给后续接手本项目的 AI Agent / 开发者使用，记录最关键的项目事实、运行方式、架构边界和修改注意事项。

## 项目定位

`fast-video-download` 当前是一个“双模式视频任务系统”：

- **传统模式**：用户输入视频 URL，解析视频信息，选择格式，创建下载任务，轮询进度，下载文件。
- **AI Agent 模式**：用户输入自然语言任务，后端执行 `Perception -> Planning -> Execution -> Reflection`，先解析视频并展示格式，用户确认格式后复用旧下载任务系统下载。

核心原则：

- 不删除旧下载流程。
- Agent 模式必须复用旧解析/下载能力，不另写一套下载器。
- 新逻辑优先放在 `backend/app/agent/`、`backend/app/tools/`、`backend/app/llm/`。
- 不把 API key、Cookie、Stripe key 写死进代码。

## 本地启动

一键启动：

```bash
cp .env.example .env
chmod +x dev.sh
./dev.sh
```

访问地址：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000
- 健康检查：http://127.0.0.1:8000/api/health

手动启动后端：

```bash
cd backend
./venv/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

手动启动前端：

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## 关键环境变量

```env
AGENT_DEMO_MODE=true
FRONTEND_BASE_URL=http://localhost:5173
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SECRET_KEY=change-me-for-local-development
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=
BILIBILI_COOKIE_FILE=
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

说明：

- `AGENT_DEMO_MODE=true`：Agent Chat 返回稳定模拟数据，不真实下载。
- `AGENT_DEMO_MODE=false`：真实调用解析工具，用户选格式后创建真实下载任务。
- `BILIBILI_COOKIE_FILE`：部分 B 站视频需要 Cookie，否则可能出现 412。

## 后端关键文件

```text
backend/main.py                         # FastAPI 入口，传统 API + Agent API
backend/downloader.py                   # 原有 yt-dlp 解析/下载逻辑
backend/douyin.py                       # 抖音解析/下载逻辑
backend/auth.py                         # JWT 认证
backend/models.py                       # 用户/VIP 数据模型
backend/database.py                     # 数据库连接
backend/app/download_tasks.py           # 共享下载任务状态

backend/app/agent/perception.py         # 自然语言 -> intent/entities/constraints
backend/app/agent/planning.py           # 规则 Planner + LLMPlanner 扩展点
backend/app/agent/execution.py          # 串行执行 plan steps
backend/app/agent/reflection.py         # 结果检查和失败诊断
backend/app/agent/orchestrator.py       # Agent 主流程编排

backend/app/tools/base.py               # Tool dataclass
backend/app/tools/registry.py           # Tool Registry
backend/app/tools/video/parse_video.py  # parse_video tool，封装旧解析逻辑
backend/app/tools/video/download_video.py # download_video tool，封装旧下载逻辑
backend/app/tools/video/parse_douyin.py # parse_douyin tool

backend/app/llm/client.py               # LLM 调用入口
```

## 前端关键文件

```text
frontend/src/App.vue                         # 首页组合 Agent 模式 + 传统模式
frontend/src/api.js                          # API 封装
frontend/src/components/AgentChat.vue        # Agent 工作台输入区和健康检查
frontend/src/components/AgentTracePanel.vue  # Agent trace、格式选择、进度和下载按钮
frontend/src/components/VideoResult.vue      # 传统模式解析结果和下载流程
frontend/src/components/AuthModal.vue        # 登录/注册
frontend/src/components/PricingModal.vue     # VIP/支付入口
```

## 传统模式请求链路

```text
用户输入 URL
-> POST /api/parse
-> VideoDownloader.parse_video 或 DouyinParser.parse
-> 前端展示格式
-> POST /api/download/prepare
-> 后端认证/VIP 限额检查
-> 创建 task_id 写入 task_status
-> 后台下载并更新进度
-> GET /api/task/status/{task_id}
-> GET /api/download/fetch/{task_id}
```

旧接口不能删除：

- `POST /api/parse`
- `POST /api/download/prepare`
- `GET /api/task/status/{task_id}`
- `GET /api/download/status/{task_id}`
- `GET /api/download/fetch/{task_id}`

## Agent 模式请求链路

```text
用户自然语言任务
-> POST /api/agent/chat
-> perception
-> planning
-> execution
-> reflection
-> 返回 Agent Trace 和 available_formats
-> 用户选择格式
-> POST /api/agent/download
-> 复用旧任务系统创建 task_id
-> 前端轮询 /api/task/status/{task_id}
-> completed 后显示 /api/download/fetch/{task_id}
```

Agent API：

- `POST /api/agent/run`：内部 Agent 调用入口。
- `POST /api/agent/chat`：聊天式 Agent 入口。
- `POST /api/agent/download`：用户选择格式后创建下载任务。
- `GET /api/health`：健康检查。

## Agent 任务语义

当前产品语义：

- “解析这个视频”或普通 URL：只执行 `parse_video`，不创建下载任务。
- “帮我下载这个视频”：先解析并推荐格式，不自动下载，等待用户确认。
- “下载 720p MP4”：识别格式 hint，尽可能匹配格式。
- “提取音频”：推荐 audio-only 格式。
- Dry run：只生成 perception 和 plan，不调用真实工具。

关键点：

- 不要让 `POST /api/agent/chat` 默认直接下载。
- 下载必须由用户选择格式后，通过 `POST /api/agent/download` 创建任务。
- 下载按钮只应在任务 `completed` 且存在 `download_url` 后出现。

## Tool Registry

当前注册工具：

- `parse_video`
- `download_video`
- `parse_douyin`

新增工具时：

1. 在 `backend/app/tools/video/` 或对应目录新增 wrapper。
2. 不复制旧业务逻辑，优先复用已有模块。
3. 在 `backend/app/tools/registry.py` 注册 tool。
4. 为 tool 添加输入 schema。
5. 补充测试。

## 测试命令

后端测试：

```bash
backend/venv/bin/python -m unittest \
  backend/test_app_agent_api.py \
  backend/test_app_orchestrator.py \
  backend/test_app_execution.py \
  backend/test_app_reflection.py \
  backend/test_app_planning.py \
  backend/test_app_perception.py \
  backend/test_app_tools.py \
  backend/test_downloader_config.py
```

Python 编译检查：

```bash
backend/venv/bin/python -m compileall backend/main.py backend/app backend/downloader.py
```

前端构建：

```bash
cd frontend
npm run build
```

## 常见错误与处理

- `yt-dlp 未安装`：执行 `backend/venv/bin/python -m pip install -r backend/requirements.txt`。
- `ffmpeg 不可用`：检查 `/api/health`，安装系统 ffmpeg 或确认 `static-ffmpeg` 可加载。
- `B 站 412`：通常是反爬或 Cookie 问题，更新 yt-dlp、配置 Cookie 或稍后重试。
- `Cookie 缺失`：设置 `BILIBILI_COOKIE_FILE`，并确认后端进程可读。
- `CORS`：确认 `.env` 里的 `FRONTEND_ORIGINS` 包含当前前端地址。
- `后端端口错误`：前端默认请求 `http://127.0.0.1:8000/api`。
- `Agent 没有直接下载`：这是预期行为。Agent 先解析，用户选格式后才下载。
- `下载按钮不出现`：只有任务 `completed` 且有 `download_url` 才显示。

## 修改注意事项

- 不要改动无关文件。
- 不要删除传统下载流程。
- 不要破坏认证、VIP、Stripe 支付逻辑。
- 不要把真实密钥、Cookie、Token 提交到 Git。
- 修改下载逻辑前先读：
  - `backend/main.py`
  - `backend/downloader.py`
  - `backend/app/download_tasks.py`
  - `frontend/src/components/VideoResult.vue`
  - `frontend/src/components/AgentTracePanel.vue`
- 如果修改 Agent 行为，需要同步检查：
  - `backend/app/agent/perception.py`
  - `backend/app/agent/planning.py`
  - `backend/app/agent/execution.py`
  - `backend/app/agent/reflection.py`
  - `backend/app/agent/orchestrator.py`
  - `backend/test_app_agent_api.py`

## 当前最近重要提交

```text
6b758e0 完善 AI Agent 模式下载闭环与文档展示
19fed0e 新增视频任务 Agent 应用层
9d677dc 补充 Agent 基础流程测试
1db82c7 新增精简版 AI Agent 基础架构
```

## 文档补充

更完整的项目协作记录见：

```text
docs/project-conversation-log.md
```
