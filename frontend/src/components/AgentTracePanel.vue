<template>
  <div class="trace-panel">
    <section class="trace-section runtime" :class="{ failed: result.ok === false }">
      <div class="section-head">
        <span class="section-index">00</span>
        <h3>运行模式与诊断</h3>
      </div>
      <div class="runtime-grid">
        <div>
          <span class="label">Mode</span>
          <strong>{{ result.mode || (result.demo_mode ? 'demo' : 'real') }}</strong>
        </div>
        <div>
          <span class="label">Status</span>
          <strong>{{ result.status || 'unknown' }}</strong>
        </div>
        <div>
          <span class="label">Dry Run</span>
          <strong>{{ result.dry_run ? '是' : '否' }}</strong>
        </div>
        <div>
          <span class="label">OK</span>
          <strong>{{ result.ok === false ? '失败' : '正常' }}</strong>
        </div>
      </div>
      <div v-if="result.error || failedStep" class="diagnostic-box">
        <strong>失败诊断</strong>
        <p>失败步骤：{{ failedStep?.id || '-' }} {{ failedStep?.tool || debug.failed_step?.tool || 'unknown' }}</p>
        <p>错误类型：{{ debug.exception_type || 'unknown' }}</p>
        <p>错误信息：{{ debug.exception_message || result.error || '无详细错误' }}</p>
        <p>建议修复：{{ repairSuggestion }}</p>
      </div>
    </section>

    <section class="trace-section">
      <div class="section-head">
        <span class="section-index">01</span>
        <h3>用户意图识别</h3>
      </div>
      <div class="intent-grid">
        <div>
          <span class="label">Intent</span>
          <strong>{{ perception.intent || 'unknown' }}</strong>
        </div>
        <div>
          <span class="label">URL</span>
          <strong>{{ perception.entities?.url || '未识别' }}</strong>
        </div>
      </div>
    </section>

    <section class="trace-section">
      <div class="section-head">
        <span class="section-index">02</span>
        <h3>Agent 计划</h3>
      </div>
      <div class="timeline">
        <div class="timeline-step" v-for="step in planSteps" :key="step.id">
          <span class="dot"></span>
          <div>
            <strong>{{ step.id }} · {{ step.tool }}</strong>
            <p>{{ formatArgs(step.args) }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="trace-section">
      <div class="section-head">
        <span class="section-index">03</span>
        <h3>工具调用过程</h3>
      </div>
      <div class="tool-grid">
        <div v-if="!executionSteps.length" class="tool-card skipped">
          <span class="tool-status">跳过</span>
          <strong>dry_run</strong>
          <p>仅生成计划，未调用真实下载工具。</p>
        </div>
        <div 
          class="tool-card" 
          v-for="(step, index) in executionSteps" 
          :key="`${step.tool}-${index}`"
          :class="{ failed: !step.ok }"
        >
          <span class="tool-status">{{ step.ok ? '完成' : '失败' }}</span>
          <strong>{{ step.tool }}</strong>
          <p>{{ step.error || step.data?.title || step.data?.filename || '工具调用已返回结果' }}</p>
        </div>
      </div>
    </section>

    <section class="trace-section reflection" :class="reflection.status">
      <div class="section-head">
        <span class="section-index">04</span>
        <h3>结果反思</h3>
      </div>
      <p>{{ reflection.reason || '暂无反思结果' }}</p>
      <span class="reflection-badge">{{ reflection.status || 'unknown' }}</span>
    </section>

    <section class="video-summary" v-if="finalVideo">
      <div>
        <span class="label">最终视频结果</span>
        <h3>{{ finalVideo.title || '未命名视频' }}</h3>
        <p>{{ finalVideo.platform || '未知平台' }}</p>
        <p>下载状态：{{ currentDownloadStatus }}</p>
        <p v-if="currentFilename">文件名：{{ currentFilename }}</p>
      </div>
      <div class="result-actions">
        <div class="format-list selectable">
          <button
            v-for="fmt in allFormats"
            :key="`${fmt.kind}-${fmt.format_id || fmt.label}`"
            type="button"
            :class="{ active: selectedFormatId === fmt.format_id }"
            :disabled="downloadState.loading"
            @click="selectFormat(fmt)"
          >
            <strong>{{ formatLabel(fmt) }}</strong>
            <small>{{ formatMeta(fmt) }}</small>
          </button>
        </div>
        <div class="selected-format" v-if="selectedFormat">
          已选择：{{ formatLabel(selectedFormat) }}
        </div>
        <button
          v-if="selectedFormat && !isDownloadCompleted"
          class="start-download-button"
          :disabled="downloadState.loading"
          @click="startDownload"
        >
          {{ downloadState.loading ? '创建任务中' : '开始下载' }}
        </button>
        <div class="download-progress" v-if="downloadState.taskId">
          <div class="progress-head">
            <strong>{{ downloadState.statusText }}</strong>
            <span>{{ downloadState.progress }}%</span>
          </div>
          <div class="progress-bar">
            <span :style="{ width: `${downloadState.progress}%` }"></span>
          </div>
          <p>
            状态：{{ downloadState.status }}
            <span v-if="downloadState.speed"> · 速度：{{ downloadState.speed }}</span>
            <span v-if="downloadState.eta"> · ETA：{{ downloadState.eta }}s</span>
          </p>
        </div>
        <p class="download-error" v-if="downloadState.error">{{ downloadState.error }}</p>
        <button
          v-if="downloadState.status === 'failed'"
          class="retry-button"
          @click="startDownload"
        >
          重试下载
        </button>
        <a
          v-if="isDownloadCompleted && downloadHref"
          class="download-button"
          :href="downloadHref"
          target="_blank"
          rel="noopener"
        >
          下载文件
        </a>
      </div>
    </section>

    <div class="next-action" v-if="result.suggested_next_action">
      {{ result.suggested_next_action }}
    </div>
  </div>
</template>

<script setup>
import { computed, onUnmounted, reactive, ref, watch } from 'vue';
import { api, BACKEND_BASE } from '../api';

const props = defineProps({
  result: {
    type: Object,
    default: () => ({})
  }
});

const perception = computed(() => props.result.perception || { entities: {} });
const planSteps = computed(() => props.result.plan?.steps || []);
const executionSteps = computed(() => props.result.execution?.steps || []);
const reflection = computed(() => props.result.reflection || {});
const finalVideo = computed(() => props.result.final_result || props.result.final_video || null);
const debug = computed(() => props.result.debug || {});
const failedStep = computed(() => debug.value.failed_step || null);
const selectedFormatId = ref('');
const selectedFormat = ref(null);
let pollTimer = null;

const downloadState = reactive({
  taskId: '',
  status: '',
  statusText: '',
  progress: 0,
  speed: '',
  eta: null,
  filename: '',
  downloadUrl: '',
  error: '',
  loading: false,
});

const allFormats = computed(() => {
  const videoFormats = (finalVideo.value?.available_formats || []).map((fmt) => ({
    ...fmt,
    kind: 'video',
    is_audio_only: false
  }));
  const audioFormats = (finalVideo.value?.audio_formats || []).map((fmt) => ({
    ...fmt,
    kind: 'audio',
    is_audio_only: true
  }));
  return [...videoFormats, ...audioFormats];
});

const currentDownloadStatus = computed(() => (
  downloadState.status || finalVideo.value?.download_status || '未下载'
));
const currentFilename = computed(() => (
  downloadState.filename || finalVideo.value?.filename || ''
));
const isDownloadCompleted = computed(() => currentDownloadStatus.value === 'completed');
const downloadHref = computed(() => {
  const downloadUrl = downloadState.downloadUrl || finalVideo.value?.download_url || '';
  if (!downloadUrl) return '';
  if (/^https?:\/\//i.test(downloadUrl)) return downloadUrl;
  return `${BACKEND_BASE}${downloadUrl.startsWith('/') ? '' : '/'}${downloadUrl}`;
});
const repairSuggestion = computed(() => {
  const message = `${debug.value.exception_message || props.result.error || ''}`.toLowerCase();
  if (message.includes('412') || message.includes('precondition')) {
    return 'B 站返回 412，通常需要更新 yt-dlp、配置 Cookie，或稍后重试。';
  }
  if (message.includes('cookie')) {
    return '检查 Cookie 文件是否存在且仍有效。';
  }
  if (message.includes('ffmpeg')) {
    return '安装 ffmpeg 并确认后端 health check 显示可用。';
  }
  if (message.includes('yt-dlp') || message.includes('ytdlp')) {
    return '确认后端虚拟环境已安装 yt-dlp，并尝试更新版本。';
  }
  return '检查 URL、平台限制、后端日志和 health check 依赖状态。';
});

const formatArgs = (args = {}) => {
  const entries = Object.entries(args);
  if (!entries.length) return '无参数';
  return entries.map(([key, value]) => `${key}: ${value}`).join(' · ');
};

const selectFormat = (fmt) => {
  selectedFormat.value = fmt;
  selectedFormatId.value = fmt.format_id;
};

const formatLabel = (fmt = {}) => {
  if (fmt.label) return fmt.label;
  const resolution = fmt.height ? `${fmt.height}P` : (fmt.kind === 'audio' ? '音频' : 'Auto');
  const ext = fmt.ext ? fmt.ext.toUpperCase() : '媒体';
  return `${resolution} · ${ext}`;
};

const formatMeta = (fmt = {}) => {
  const parts = [];
  if (fmt.format_id) parts.push(`ID ${fmt.format_id}`);
  if (fmt.filesize) parts.push(formatBytes(fmt.filesize));
  if (fmt.resolution) parts.push(fmt.resolution);
  return parts.join(' · ') || '可用格式';
};

const formatBytes = (bytes) => {
  if (!bytes) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = Number(bytes);
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
};

const startDownload = async () => {
  if (!selectedFormat.value || !perception.value.entities?.url) return;

  clearPollTimer();
  downloadState.loading = true;
  downloadState.error = '';
  downloadState.status = 'pending';
  downloadState.statusText = '正在创建下载任务';
  downloadState.progress = 0;
  downloadState.downloadUrl = '';
  downloadState.filename = '';

  try {
    const task = await api.agentDownload(
      perception.value.entities.url,
      selectedFormat.value.format_id,
      Boolean(selectedFormat.value.is_audio_only),
      props.result.session_id || 'frontend-agent-demo'
    );
    downloadState.taskId = task.task_id;
    downloadState.status = task.status || 'pending';
    downloadState.statusText = '任务已创建，等待下载';
    downloadState.progress = task.progress || 0;
    pollDownloadStatus();
  } catch (err) {
    downloadState.status = 'failed';
    downloadState.statusText = '任务创建失败';
    downloadState.error = err.message || 'Agent 下载任务创建失败';
  } finally {
    downloadState.loading = false;
  }
};

const pollDownloadStatus = async () => {
  if (!downloadState.taskId) return;

  try {
    const data = await api.getTaskStatus(downloadState.taskId);
    downloadState.status = data.status || 'unknown';
    downloadState.progress = Math.floor(data.progress || 0);
    downloadState.speed = data.speed || '';
    downloadState.eta = data.eta;
    downloadState.filename = data.filename || downloadState.filename;
    downloadState.downloadUrl = data.download_url || downloadState.downloadUrl;
    downloadState.error = data.error || '';

    if (data.status === 'completed') {
      downloadState.progress = 100;
      downloadState.statusText = '下载完成，可以获取文件';
      return;
    }
    if (data.status === 'failed') {
      downloadState.statusText = '下载失败';
      downloadState.error = data.error || data.message || '下载任务失败';
      return;
    }
    if (data.status === 'merging') {
      downloadState.statusText = '正在合并音视频';
      downloadState.progress = Math.max(downloadState.progress, 99);
    } else {
      downloadState.statusText = data.message || '正在下载';
    }
    pollTimer = window.setTimeout(pollDownloadStatus, 1500);
  } catch (err) {
    downloadState.status = 'failed';
    downloadState.statusText = '查询进度失败';
    downloadState.error = err.message || '查询下载进度失败';
  }
};

const clearPollTimer = () => {
  if (pollTimer) {
    window.clearTimeout(pollTimer);
    pollTimer = null;
  }
};

watch(finalVideo, (video) => {
  clearPollTimer();
  downloadState.taskId = video?.task_id || '';
  downloadState.status = video?.download_status || '';
  downloadState.statusText = video?.download_status === 'completed' ? '下载完成，可以获取文件' : '';
  downloadState.progress = video?.download_status === 'completed' ? 100 : 0;
  downloadState.speed = '';
  downloadState.eta = null;
  downloadState.filename = video?.filename || '';
  downloadState.downloadUrl = video?.download_url || '';
  downloadState.error = '';

  const recommended = video?.recommended_format;
  const firstFormat = allFormats.value[0];
  const nextFormat = recommended || firstFormat || null;
  selectedFormat.value = nextFormat;
  selectedFormatId.value = nextFormat?.format_id || '';
  if (downloadState.taskId && !['completed', 'failed'].includes(downloadState.status)) {
    pollDownloadStatus();
  }
}, { immediate: true });

onUnmounted(clearPollTimer);
</script>

<style scoped>
.trace-panel {
  display: grid;
  gap: 14px;
}

.trace-section,
.video-summary,
.next-action {
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(15, 23, 42, 0.72);
  border-radius: 10px;
  padding: 18px;
}

.runtime {
  border-color: rgba(34, 211, 238, 0.28);
}

.runtime.failed {
  border-color: rgba(248, 113, 113, 0.42);
}

.runtime-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.diagnostic-box {
  margin-top: 12px;
  border: 1px solid rgba(248, 113, 113, 0.28);
  border-radius: 8px;
  padding: 12px;
  background: rgba(127, 29, 29, 0.22);
}

.diagnostic-box strong {
  color: #fecaca;
}

.diagnostic-box p {
  color: rgba(254, 226, 226, 0.86);
  margin: 6px 0 0;
  overflow-wrap: anywhere;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.section-index {
  color: #22d3ee;
  font-size: 0.78rem;
  font-weight: 800;
}

.section-head h3,
.video-summary h3 {
  font-size: 1rem;
  margin: 0;
}

.intent-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.5fr) minmax(0, 1.5fr);
  gap: 12px;
}

.label {
  display: block;
  color: rgba(226, 232, 240, 0.52);
  font-size: 0.78rem;
  margin-bottom: 4px;
}

.intent-grid strong,
.timeline strong,
.tool-card strong {
  color: #f8fafc;
  overflow-wrap: anywhere;
}

.timeline {
  display: grid;
  gap: 12px;
}

.timeline-step {
  display: grid;
  grid-template-columns: 14px 1fr;
  gap: 10px;
  align-items: start;
}

.dot {
  width: 10px;
  height: 10px;
  margin-top: 7px;
  border-radius: 999px;
  background: #22d3ee;
  box-shadow: 0 0 0 5px rgba(34, 211, 238, 0.12);
}

.timeline p,
.tool-card p,
.reflection p,
.video-summary p {
  color: rgba(226, 232, 240, 0.68);
  font-size: 0.86rem;
  margin-top: 4px;
  overflow-wrap: anywhere;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.tool-card {
  border: 1px solid rgba(34, 211, 238, 0.22);
  background: rgba(8, 47, 73, 0.35);
  border-radius: 8px;
  padding: 14px;
}

.tool-card.failed {
  border-color: rgba(239, 68, 68, 0.35);
  background: rgba(127, 29, 29, 0.25);
}

.tool-card.skipped {
  border-color: rgba(250, 204, 21, 0.32);
  background: rgba(113, 63, 18, 0.22);
}

.tool-status,
.reflection-badge {
  display: inline-flex;
  margin-bottom: 8px;
  color: #67e8f9;
  font-size: 0.78rem;
  font-weight: 700;
}

.reflection.ok {
  border-color: rgba(34, 197, 94, 0.35);
}

.reflection.needs_repair {
  border-color: rgba(250, 204, 21, 0.4);
}

.video-summary {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.16), rgba(37, 99, 235, 0.14));
}

.format-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.result-actions {
  display: grid;
  gap: 12px;
  justify-items: end;
}

.format-list button {
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  padding: 7px 11px;
  color: #e0f2fe;
  background: rgba(15, 23, 42, 0.45);
  font-size: 0.78rem;
  cursor: pointer;
  text-align: left;
}

.format-list button.active {
  border-color: #67e8f9;
  background: rgba(34, 211, 238, 0.18);
  color: #fff;
}

.format-list button strong,
.format-list button small {
  display: block;
}

.format-list button small {
  color: rgba(226, 232, 240, 0.58);
  font-size: 0.7rem;
  margin-top: 2px;
}

.download-button {
  border: none;
  border-radius: 999px;
  color: #082f49;
  background: #67e8f9;
  font-weight: 900;
  padding: 9px 14px;
  text-decoration: none;
}

.start-download-button,
.retry-button {
  border: none;
  border-radius: 999px;
  color: #082f49;
  background: #fbbf24;
  font-weight: 900;
  padding: 9px 14px;
  cursor: pointer;
}

.selected-format {
  color: #e0f2fe;
  font-size: 0.82rem;
}

.download-progress {
  min-width: 260px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  padding: 12px;
  background: rgba(2, 6, 23, 0.36);
}

.progress-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #e2e8f0;
  font-size: 0.82rem;
}

.progress-bar {
  height: 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.22);
  overflow: hidden;
  margin-top: 8px;
}

.progress-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #22d3ee, #fbbf24);
}

.download-progress p,
.download-error {
  color: rgba(226, 232, 240, 0.68);
  font-size: 0.78rem;
  margin: 8px 0 0;
}

.download-error {
  color: #fecaca;
}

.next-action {
  color: #e0f2fe;
  border-color: rgba(34, 211, 238, 0.24);
}

@media (max-width: 720px) {
  .intent-grid,
  .runtime-grid,
  .video-summary {
    grid-template-columns: 1fr;
    display: grid;
  }

  .format-list {
    justify-content: flex-start;
  }

  .result-actions {
    justify-items: start;
  }
}
</style>
