<template>
  <section class="features-section">
    <div class="features-grid">
      <div class="feature-card glass-panel" v-for="(feat, idx) in features" :key="idx">
        <div class="icon-wrapper">
            <span class="icon">{{ feat.icon }}</span>
        </div>
        <h3 class="title">{{ feat.title }}</h3>
        <p class="desc">{{ feat.desc }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  {
    icon: '⚡',
    title: '1800+ 平台支持',
    desc: '基于强大的 yt-dlp 引擎，支持主流平台包括 YouTube, Bilibili, 抖音, X/Twitter 等，几乎覆盖全网。'
  },
  {
    icon: '🔒',
    title: '安全且纯粹',
    desc: '所有解析均在服务端或本地进行。没有烦人的广告，没有隐藏的弹窗，给你最极客的下载体验。'
  },
  {
    icon: '✨',
    title: '多画质自由选',
    desc: '从 4K 超清到 480P 标清，或是纯音频提取，自由掌控你的下载需求。'
  }
];
</script>

<style scoped>
.features-section {
  padding: 60px 0;
  margin-top: 40px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.feature-card {
  padding: 32px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  background: rgba(255, 255, 255, 0.02);
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(255,255,255,0.1);
  background: rgba(255, 255, 255, 0.04);
}

.icon-wrapper {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 20px;
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.title {
  font-size: 1.2rem;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.desc {
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.95rem;
}
</style>
