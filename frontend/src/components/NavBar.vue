<template>
  <nav class="navbar glass-panel">
    <div class="nav-content">
      <div class="logo">
        <span class="logo-icon">⚡</span>
        <span class="logo-text">Fast Video <span class="text-gradient">Download</span></span>
      </div>
      <div class="nav-links">
        <a href="https://github.com/ZKQuinn" target="_blank" class="github-link">
          GitHub
        </a>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 70px;
  border-radius: 0;
  border-left: none;
  border-right: none;
  border-top: none;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.3s ease;
}

.nav-content {
  width: 100%;
  max-width: 1200px;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.logo-icon {
  font-size: 1.5rem;
}

.github-link {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color 0.2s ease;
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
}

.github-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.1);
}
</style>
