<template>
  <div class="video-result glass-panel" v-if="video && video.formats">
    <!--Progress Status Overlay -->
    <transition name="fade">
      <div v-if="taskProgress.show" class="task-overlay">
         <div class="task-card glass-panel">
            <div class="task-header">
               <div class="spinner-container">
                  <div v-if="taskProgress.status !== 'completed' && taskProgress.status !== 'failed'" class="premium-loader"></div>
                  <div v-else-if="taskProgress.status === 'completed'" class="success-icon">
                    <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="3" fill="none"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  </div>
                  <div v-else-if="taskProgress.status === 'failed'" class="error-icon">
                    <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="3" fill="none"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                  </div>
               </div>
               <div class="task-title-group">
                  <h3>{{ taskProgress.statusText }}</h3>
                  <p class="task-filename" v-if="video.title">{{ video.title }}</p>
               </div>
            </div>
            
            <div class="task-body" v-if="taskProgress.status !== 'failed'">
               <div class="progress-bar-container">
                  <div class="progress-bar-fill" :style="{ width: taskProgress.percent + '%' }"></div>
               </div>
               <div class="progress-stats">
                  <span class="percent">{{ taskProgress.percent }}%</span>
                  <span class="speed" v-if="taskProgress.speed">{{ taskProgress.speed }}</span>
               </div>
            </div>
            
            <div class="task-error" v-if="taskProgress.status === 'failed'">
               <p>{{ taskProgress.errorMsg }}</p>
               <button class="btn-secondary btn-small" @click="taskProgress.show = false">Close</button>
            </div>
         </div>
      </div>
    </transition>

    <div class="video-header">
       <div class="thumbnail-wrapper">
           <img :src="thumbnailUrl" :alt="video.title" v-if="thumbnailUrl" class="thumbnail-img" />
           <div class="duration-badge" v-if="video.duration_string">{{ video.duration_string }}</div>
       </div>
       <div class="video-info">
           <h2 class="video-title">{{ video.title || t.videoResult.videoTitlePlaceholder }}</h2>
           <div class="meta-row">
               <div class="meta-item uploader" v-if="video.uploader">
                   <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                   <span>{{ video.uploader }}</span>
               </div>
               <div class="meta-item platform">
                   <span class="platform-tag">{{ video.platform || t.videoResult.unknown }}</span>
               </div>
           </div>
       </div>
    </div>

    <div class="formats-section">
        <h3 class="section-title">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
          {{ t.videoResult.videoFormatsTitle }}
        </h3>
        
        <div class="format-grid">
            <label 
              v-for="fmt in videoFormats" 
              :key="fmt.format_id"
              class="format-card"
              :class="{ active: selectedFormat === fmt.format_id }"
            >
                <input 
                  type="radio" 
                  name="format" 
                  :value="fmt.format_id" 
                  v-model="selectedFormat"
                />
                <div class="format-content">
                    <div class="res-badge">{{ fmt.height && fmt.height < 9999 ? fmt.height + t.videoResult.resUnit : t.videoResult.auto }}</div>
                    <div class="format-main">
                      <span class="ext-tag">{{ fmt.ext?.toUpperCase() }}</span>
                      <span class="filesize" v-if="fmt.filesize">{{ formatBytes(fmt.filesize) }}</span>
                    </div>
                </div>
                <div class="check-mark">
                   <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="3" fill="none"><polyline points="20 6 9 17 4 12"></polyline></svg>
                </div>
            </label>
        </div>
        
        <div class="actions">
            <button class="btn-primary btn-large download-trigger" @click="handleDownload" :disabled="taskProgress.show || !selectedFormat">
                <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="2.5" fill="none" class="download-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span>{{ t.videoResult.downloadButton }}</span>
            </button>
            <transition name="fade">
              <div class="error-msg" v-if="error">{{ error }}</div>
            </transition>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue';
import { api } from '../api';
import { useI18n } from '../i18n';

// 国际化文案
const { t } = useI18n();

// 定义属性
const props = defineProps({
    video: {
        type: Object,
        default: null
    },
    url: {
        type: String,
        default: ''
    }
});

// UI 状态变量
const selectedFormat = ref(''); 
const error = ref('');

// 任务进度追踪
const taskProgress = reactive({
    show: false,
    percent: 0,
    statusText: '',
    speed: '',
    status: 'idle',
    errorMsg: ''
});

// 处理封面图的计算属性
const thumbnailUrl = computed(() => {
    if (!props.video || !props.video.thumbnail) return '';
    return api.getProxyUrl(props.video.thumbnail);
});

const videoFormats = computed(() => {
    if (!props.video) return [];
    return props.video.formats || [];
});

watch(() => props.video, (newVal) => {
    if (newVal && newVal.formats && newVal.formats.length > 0) {
        const vids = videoFormats.value;
        if (vids.length > 0) {
            selectedFormat.value = vids[0].format_id;
        } else if (newVal.formats.length > 0) {
            selectedFormat.value = newVal.formats[0].format_id;
        }
    } else {
        selectedFormat.value = '';
    }
    error.value = '';
}, { immediate: true });

const formatBytes = (bytes, decimals = 2) => {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

/**
 * 处理下载：三阶段流程 (Prepare -> Status -> Fetch)
 */
const handleDownload = async () => {
    if (!selectedFormat.value) return;
    
    error.value = '';
    taskProgress.show = true;
    taskProgress.status = 'preparing';
    taskProgress.percent = 0;
    taskProgress.statusText = t.value.videoResult.preparingOnServer;
    taskProgress.speed = '';
    
    try {
        // 1. 创建任务
        const { task_id } = await api.prepareDownload(props.url, selectedFormat.value, false);
        
        // 2. 开始轮询
        const poll = async () => {
            try {
                const data = await api.getTaskStatus(task_id);
                taskProgress.status = data.status;
                taskProgress.percent = Math.floor(data.progress || 0);
                taskProgress.speed = data.speed || '';
                
                if (data.status === 'downloading') {
                    taskProgress.statusText = data.download_type === 'audio' 
                        ? t.value.videoResult.downloadingAudioStep 
                        : t.value.videoResult.downloadingVideoStep;
                } else if (data.status === 'merging') {
                    taskProgress.statusText = t.value.videoResult.merging;
                    taskProgress.percent = 99;
                } else if (data.status === 'completed') {
                    taskProgress.statusText = t.value.videoResult.ready;
                    taskProgress.percent = 100;
                    api.downloadFile(task_id);
                    setTimeout(() => { taskProgress.show = false; }, 3000);
                    return;
                } else if (data.status === 'failed') {
                    taskProgress.status = 'failed';
                    taskProgress.errorMsg = data.error || 'Task failed';
                    return;
                }
                setTimeout(poll, 1500);
            } catch (e) {
                taskProgress.status = 'failed';
                taskProgress.errorMsg = 'Polling failed: ' + e.message;
            }
        };
        await poll();
    } catch (err) {
        taskProgress.status = 'failed';
        taskProgress.errorMsg = err.message;
        error.value = err.message || t.value.videoResult.errorDownloadFailed;
    }
};
</script>

<style scoped>
.video-result {
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Task Overlay */
.task-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 100;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(20px);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 32px;
}

.task-card {
  width: 100%;
  max-width: 480px;
  padding: 40px;
  text-align: left;
  border-radius: 24px;
}

.task-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 32px;
}

.premium-loader {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

.success-icon, .error-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
}

.success-icon { background: #10b981; }
.error-icon { background: #ef4444; }

.task-title-group h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: #fff;
}

.task-filename {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.5);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.progress-bar-container {
  height: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 100px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-bar-fill {
  height: 100%;
  background: var(--gradient-primary);
  transition: width 0.4s cubic-bezier(0.1, 0.5, 0.1, 1);
  box-shadow: 0 0 15px var(--color-primary-glow);
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
}

/* Video Header */
.video-header {
  display: flex;
  padding: 32px;
  gap: 32px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.thumbnail-wrapper {
  position: relative;
  width: 320px;
  aspect-ratio: 16/9;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.duration-badge {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(4px);
  color: #fff;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
}

.video-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
}

.video-title {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.35;
  margin-bottom: 16px;
  color: #fff;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta-row {
  display: flex;
  gap: 16px;
  align-items: center;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.5);
}

.platform-tag {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #fff;
}

/* Formats */
.formats-section {
  padding: 32px;
}

.section-title {
  font-size: 1.15rem;
  margin-bottom: 24px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}

.format-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 40px;
}

.format-card {
  position: relative;
  cursor: pointer;
}

.format-card input { display: none; }

.format-content {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.res-badge {
  font-size: 1.25rem;
  font-weight: 800;
  color: #fff;
}

.format-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ext-tag {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
}

.filesize {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-primary);
}

.check-mark {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  background: var(--color-primary);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #fff;
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.2s ease;
}

.format-card:hover .format-content {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
}

.format-card.active .format-content {
  background: rgba(236, 72, 153, 0.05);
  border-color: var(--color-primary);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.format-card.active .check-mark {
  opacity: 1;
  transform: scale(1);
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.download-trigger {
  width: 100%;
  max-width: 320px;
}

.download-icon {
  margin-right: 8px;
}

.error-msg {
  color: #ef4444;
  font-size: 0.95rem;
  padding: 12px 20px;
  background: rgba(239, 68, 68, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.1);
}

@media (max-width: 768px) {
  .video-header {
    flex-direction: column;
    padding: 24px;
    gap: 24px;
  }
  
  .thumbnail-wrapper {
    width: 100%;
  }
  
  .video-title {
    font-size: 1.25rem;
  }
}

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
