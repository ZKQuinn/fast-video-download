<template>
  <div class="video-result glass-panel" v-if="video && video.formats">
    <div class="video-header">
       <div class="thumbnail">
           <img :src="thumbnailUrl" :alt="video.title" v-if="thumbnailUrl" />
           <div class="duration" v-if="video.duration_string">{{ video.duration_string }}</div>
       </div>
       <div class="video-info">
           <h2 class="title">{{ video.title || '未知标题' }}</h2>
           <div class="meta">
               <span class="author" v-if="video.uploader">
                   <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                   {{ video.uploader }}
               </span>
               <span class="platform">
                   Platform: <strong>{{ video.platform || 'Unknown' }}</strong>
               </span>
           </div>
       </div>
    </div>

    <div class="formats-section">
        <h3>Select Quality</h3>
        
        <div class="format-groups">
            <!-- Video Formats -->
            <div class="format-group" v-if="videoFormats.length">
                <h4 class="group-title">
                  <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                  Video
                </h4>
                <div class="format-list">
                    <label 
                      v-for="fmt in videoFormats" 
                      :key="fmt.format_id"
                      class="format-item"
                      :class="{ active: selectedFormat === fmt.format_id }"
                    >
                        <input 
                          type="radio" 
                          name="format" 
                          :value="fmt.format_id" 
                          v-model="selectedFormat"
                          @change="isAudioOnly = false"
                        />
                        <div class="format-details">
                            <span class="resolution">{{ fmt.label || (fmt.height ? fmt.height + 'p' : 'Auto') }}</span>
                            <span class="ext">{{ fmt.ext }}</span>
                            <span class="size" v-if="fmt.filesize">{{ formatBytes(fmt.filesize) }}</span>
                            <span class="features" v-if="fmt.has_audio"><small>✓ Audio</small></span>
                            <span class="features muted" v-else><small>✕ No Audio</small></span>
                        </div>
                    </label>
                </div>
            </div>

            <!-- Audio Formats -->
            <div class="format-group" v-if="audioFormats.length">
                <h4 class="group-title">
                  <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                  Audio Only
                </h4>
                <div class="format-list">
                    <label 
                      v-for="fmt in audioFormats" 
                      :key="fmt.format_id"
                      class="format-item"
                      :class="{ active: selectedFormat === fmt.format_id }"
                    >
                        <input 
                          type="radio" 
                          name="format" 
                          :value="fmt.format_id" 
                          v-model="selectedFormat"
                          @change="isAudioOnly = true"
                        />
                        <div class="format-details">
                            <span class="resolution">{{ fmt.ext }}</span>
                            <span class="ext">{{ fmt.abr ? Math.round(fmt.abr) + 'kbps' : 'Auto' }}</span>
                            <span class="size" v-if="fmt.filesize">{{ formatBytes(fmt.filesize) }}</span>
                        </div>
                    </label>
                </div>
            </div>
        </div>
        
        <div class="actions">
            <button class="btn-download" @click="handleDownload" :disabled="downloading || !selectedFormat">
                <span class="icon">
                    <svg v-if="!downloading" viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    <svg v-else class="spin" viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
                </span>
                {{ downloading ? 'Downloading...' : 'Download File' }}
            </button>
            <div class="error-msg" v-if="error">{{ error }}</div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { api } from '../api';

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

const selectedFormat = ref('');
const isAudioOnly = ref(false);
const downloading = ref(false);
const error = ref('');

const thumbnailUrl = computed(() => {
    if (!props.video || !props.video.thumbnail) return '';
    return api.getProxyUrl(props.video.thumbnail);
});

const videoFormats = computed(() => {
    if (!props.video || !props.video.formats) return [];
    return props.video.formats.filter(f => {
        const vcodec = f.vcodec || '';
        return vcodec !== 'none' && vcodec !== '';
    });
});

const audioFormats = computed(() => {
    if (!props.video || !props.video.formats) return [];
    return props.video.formats.filter(f => {
        const vcodec = f.vcodec || '';
        const acodec = f.acodec || '';
        return vcodec === 'none' && acodec !== 'none' && acodec !== '';
    });
});

// Auto-select best format when video changes (must be after videoFormats declaration)
watch(() => props.video, (newVal) => {
    if (newVal && newVal.formats && newVal.formats.length > 0) {
        const vids = videoFormats.value;
        if (vids.length > 0) {
            selectedFormat.value = vids[0].format_id;
            isAudioOnly.value = false;
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

const handleDownload = async () => {
    if (!selectedFormat.value) return;
    
    downloading.value = true;
    error.value = '';
    
    try {
        await api.downloadVideo(props.url, selectedFormat.value, isAudioOnly.value);
    } catch (err) {
        error.value = err.message || 'Download failed. Please try again.';
    } finally {
        downloading.value = false;
    }
};
</script>

<style scoped>
.video-result {
  max-width: 800px;
  margin: 0 auto 40px auto;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  animation: slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

.video-header {
  display: flex;
  padding: 24px;
  gap: 24px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(0,0,0,0.2);
}

.thumbnail {
  position: relative;
  width: 280px;
  height: 158px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  backdrop-filter: blur(4px);
}

.video-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.title {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 16px;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.author {
  display: flex;
  align-items: center;
  gap: 6px;
}

.formats-section {
  padding: 24px;
}

.formats-section h3 {
  font-size: 1.1rem;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.format-groups {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 32px;
}

.group-title {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.format-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.format-item {
  display: block;
  cursor: pointer;
}

.format-item input {
  display: none;
}

.format-details {
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.2s ease;
}

.format-item:hover .format-details {
  border-color: var(--border-hover);
  background: rgba(255, 255, 255, 0.05);
}

.format-item.active .format-details {
  border-color: var(--accent-purple);
  background: rgba(102, 126, 234, 0.1);
  box-shadow: inset 0 0 0 1px var(--accent-purple), 0 4px 12px rgba(102, 126, 234, 0.2);
}

.resolution {
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-primary);
}

.ext {
  color: var(--text-secondary);
  font-size: 0.85rem;
  text-transform: uppercase;
}

.size {
  color: var(--accent-blue);
  font-size: 0.85rem;
  font-weight: 500;
}

.features {
  margin-top: 4px;
  color: #4ade80;
}
.features.muted {
  color: var(--text-muted);
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.btn-download {
  width: 100%;
  max-width: 300px;
  background: var(--text-primary);
  color: var(--bg-primary);
  font-weight: 600;
  font-size: 1.1rem;
  padding: 16px;
  border-radius: 14px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-download:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
  background: var(--gradient-cta);
  color: white;
}

.btn-download:active:not(:disabled) {
  transform: translateY(0);
}

.btn-download:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: rgba(255,255,255,0.1);
  color: var(--text-secondary);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

.error-msg {
  color: #f87171;
  font-size: 0.9rem;
  background: rgba(248, 113, 113, 0.1);
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid rgba(248, 113, 113, 0.2);
}

/* 响应式 */
@media (max-width: 768px) {
  .video-header {
    flex-direction: column;
    padding: 16px;
  }
  .thumbnail {
    width: 100%;
    height: auto;
    aspect-ratio: 16/9;
  }
  .formats-section {
    padding: 16px;
  }
  .btn-download {
    max-width: 100%;
  }
}
</style>
