<template>
  <section class="agent-workbench">
    <div class="workbench-header">
      <div>
        <span class="eyebrow">AI Agent 模式</span>
        <h2>视频任务工作台</h2>
        <p>用自然语言描述任务，查看 Agent 如何识别意图、制定计划、调用工具并反思结果。</p>
      </div>
      <div class="status-stack">
        <div class="mode-pill" :class="{ real: currentMode === 'Real Mode' }">{{ currentMode }}</div>
        <button class="health-refresh" @click="loadHealth" :disabled="loadingHealth">
          {{ loadingHealth ? '检查中' : '刷新健康状态' }}
        </button>
      </div>
    </div>

    <div class="workbench-body">
      <div class="command-panel">
        <div class="health-panel">
          <div>
            <span>后端</span>
            <strong>{{ health?.backend?.status || health?.status || 'unknown' }}</strong>
          </div>
          <div>
            <span>yt-dlp</span>
            <strong :class="{ bad: health && !health?.yt_dlp?.available }">{{ yesNo(health?.yt_dlp?.available) }}</strong>
          </div>
          <div>
            <span>ffmpeg</span>
            <strong :class="{ bad: health && !health?.ffmpeg?.available }">{{ yesNo(health?.ffmpeg?.available) }}</strong>
          </div>
          <div>
            <span>Demo</span>
            <strong>{{ health?.demo_mode ? '开启' : '关闭' }}</strong>
          </div>
        </div>

        <label for="agent-message">任务指令</label>
        <textarea
          id="agent-message"
          v-model="message"
          :disabled="loading"
          rows="5"
          placeholder="例如：帮我下载这个视频 https://example.com/video，并告诉我 Agent 做了哪些步骤"
        ></textarea>

        <div class="context-row">
          <input 
            v-model="url"
            :disabled="loading"
            placeholder="可选：视频 URL，会作为上下文传给 Agent"
          />
          <button @click="runAgent(false)" :disabled="loading || !message.trim()">
            {{ loading ? '执行中' : '运行 Agent' }}
          </button>
        </div>
        <button class="dry-run-button" @click="runAgent(true)" :disabled="loading || !message.trim()">
          仅生成计划
        </button>

        <p class="agent-error" v-if="error">{{ error }}</p>

        <div class="quick-actions">
          <button @click="fillDemo('download')" :disabled="loading">下载视频演示</button>
          <button @click="fillDemo('audio')" :disabled="loading">提取音频演示</button>
          <button @click="fillDemo('parse')" :disabled="loading">解析信息演示</button>
        </div>
      </div>

      <AgentTracePanel v-if="result" :result="result" />
      <div v-else class="empty-trace">
        <span>等待任务</span>
        <p>运行后这里会显示意图识别、计划、工具调用、反思和最终视频结果。</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { api } from '../api';
import AgentTracePanel from './AgentTracePanel.vue';

const message = ref('帮我下载这个视频');
const url = ref('https://www.bilibili.com/video/BV1AgentDemo/');
const loading = ref(false);
const loadingHealth = ref(false);
const error = ref('');
const result = ref(null);
const health = ref(null);

const currentMode = computed(() => {
  if (result.value?.mode === 'real') return 'Real Mode';
  if (result.value?.mode === 'demo' || result.value?.demo_mode) return 'Demo Mode';
  if (health.value?.demo_mode === false) return 'Real Mode';
  return 'Demo Mode';
});

const runAgent = async (dryRun = false) => {
  error.value = '';
  loading.value = true;
  try {
    const context = url.value.trim() ? { url: url.value.trim() } : {};
    result.value = await api.agentChat(message.value, context, 'frontend-agent-demo', { dryRun });
  } catch (err) {
    error.value = err.message || 'Agent 请求失败';
  } finally {
    loading.value = false;
  }
};

const loadHealth = async () => {
  loadingHealth.value = true;
  try {
    health.value = await api.getHealth();
  } catch (err) {
    health.value = {
      status: 'failed',
      backend: { status: 'unreachable' },
      yt_dlp: { available: false },
      ffmpeg: { available: false },
      error: err.message || '健康检查失败'
    };
  } finally {
    loadingHealth.value = false;
  }
};

const yesNo = (value) => {
  if (value === true) return '可用';
  if (value === false) return '不可用';
  return '未知';
};

const fillDemo = (type) => {
  url.value = 'https://www.bilibili.com/video/BV1AgentDemo/';
  if (type === 'audio') {
    message.value = '帮我提取这个视频的音频';
  } else if (type === 'parse') {
    message.value = '解析这个视频的信息和可用格式';
  } else {
    message.value = '帮我下载这个视频';
  }
};

onMounted(loadHealth);
</script>

<style scoped>
.agent-workbench {
  width: min(1180px, calc(100% - 40px));
  margin: 100px auto 48px;
  border: 1px solid rgba(34, 211, 238, 0.18);
  background: linear-gradient(180deg, rgba(8, 47, 73, 0.72), rgba(15, 23, 42, 0.82));
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.42);
}

.workbench-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.eyebrow {
  color: #67e8f9;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.workbench-header h2 {
  margin: 6px 0 8px;
  font-size: clamp(1.8rem, 4vw, 3.2rem);
  line-height: 1.05;
}

.workbench-header p {
  color: rgba(226, 232, 240, 0.68);
  max-width: 680px;
}

.mode-pill {
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 999px;
  padding: 8px 12px;
  color: #67e8f9;
  font-weight: 800;
  white-space: nowrap;
}

.mode-pill.real {
  color: #fbbf24;
  border-color: rgba(251, 191, 36, 0.38);
}

.status-stack {
  display: grid;
  gap: 10px;
  justify-items: end;
}

.health-refresh,
.dry-run-button {
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(15, 23, 42, 0.72);
  color: #e2e8f0;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 800;
  padding: 8px 12px;
}

.workbench-body {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(0, 1.35fr);
  gap: 18px;
}

.command-panel,
.empty-trace {
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(2, 6, 23, 0.46);
  border-radius: 10px;
  padding: 20px;
}

.command-panel label {
  display: block;
  color: #e2e8f0;
  font-weight: 700;
  margin-bottom: 10px;
}

.health-panel {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 18px;
}

.health-panel div {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 8px;
  padding: 10px;
  background: rgba(15, 23, 42, 0.62);
}

.health-panel span {
  display: block;
  color: rgba(226, 232, 240, 0.52);
  font-size: 0.76rem;
  margin-bottom: 4px;
}

.health-panel strong {
  color: #86efac;
  font-size: 0.9rem;
}

.health-panel strong.bad {
  color: #fca5a5;
}

textarea,
.context-row input {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.86);
  color: #fff;
  outline: none;
}

textarea {
  resize: vertical;
  min-height: 128px;
  padding: 14px;
  line-height: 1.5;
}

.context-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  margin-top: 12px;
}

.context-row input {
  padding: 12px;
}

.context-row button,
.quick-actions button {
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 800;
}

.context-row button {
  min-width: 120px;
  padding: 0 16px;
  color: #082f49;
  background: #67e8f9;
}

.dry-run-button {
  width: 100%;
  margin-top: 10px;
  border-radius: 8px;
}

.context-row button:disabled,
.quick-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.quick-actions button {
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.18);
  padding: 8px 10px;
}

.agent-error {
  color: #fca5a5;
  margin-top: 10px;
}

.empty-trace {
  min-height: 360px;
  display: grid;
  place-content: center;
  text-align: center;
  color: rgba(226, 232, 240, 0.6);
}

.empty-trace span {
  color: #e2e8f0;
  font-size: 1.1rem;
  font-weight: 800;
}

@media (max-width: 900px) {
  .agent-workbench {
    width: min(100% - 24px, 1180px);
    margin-top: 88px;
    padding: 18px;
  }

  .workbench-header,
  .workbench-body,
  .context-row,
  .health-panel {
    grid-template-columns: 1fr;
    display: grid;
  }

  .status-stack {
    justify-items: start;
  }

  .context-row button {
    min-height: 44px;
  }
}
</style>
