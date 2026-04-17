<template>
  <footer class="footer">
    <div class="footer-content">
      <div class="footer-logo">⚡ Fast Video Download</div>
      <p class="copyright">
        Made with <span class="heart">❤️</span> for you.<br/>
        Powered by yt-dlp & Vue 3.
      </p>
      <div class="disclaimer">
        Disclaimer: This tool is for personal and educational use only.<br/>
        Please respect copyright laws and the terms of service of the respective platforms.
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  margin-top: 100px;
  padding: 60px 24px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-secondary);
  text-align: center;
}

.footer-content {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.footer-logo {
  font-weight: 700;
  font-size: 1.2rem;
  color: var(--text-primary);
}

.copyright {
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.5;
}

.heart {
  color: #ff4b4b;
}

.disclaimer {
  margin-top: 24px;
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.6;
}
</style>
