<template>
  <footer class="footer">
    <div class="footer-content">
      <div class="footer-logo">⚡ Fast Video Download</div>
      <p class="copyright">
        {{ t.footer.madeWith }} <span class="heart">❤️</span> {{ t.footer.forYou }}.<br/>
        {{ t.footer.poweredBy }}
      </p>
      <div class="disclaimer">
        {{ t.footer.disclaimer1 }}<br/>
        {{ t.footer.disclaimer2 }}
      </div>
      <div class="copyright-bar">
        {{ t.footer.copyRight }}
      </div>
    </div>
  </footer>
</template>

<script setup>
import { useI18n } from '../i18n';
const { t } = useI18n();
</script><style scoped>
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

.copyright-bar {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.85rem;
  color: var(--text-muted);
  opacity: 0.8;
}
</style>
