<template>
  <div class="menu-container">
    <nav class="menu-grid" role="navigation" aria-label="User menu">
      <!-- Edit Profile -->
      <button 
        class="menu-item"
        @click="handleEditProfile"
        aria-label="Edit Profile"
      >
        <div class="menu-content">
          <div class="icon-wrapper">
            <md-icon>person_edit</md-icon>
            <div class="icon-background"></div>
          </div>
          <span class="menu-label">Edit Profile</span>
        </div>
        <span class="menu-ripple"></span>
      </button>

      <!-- Manage Barcode -->
      <button 
        class="menu-item"
        @click="handleManageBarcode"
        aria-label="Manage Barcode"
      >
        <div class="menu-content">
          <div class="icon-wrapper">
            <md-icon>qr_code_scanner</md-icon>
            <div class="icon-background"></div>
          </div>
          <span class="menu-label">Manage Barcode</span>
        </div>
        <span class="menu-ripple"></span>
      </button>

      <!-- Log Out -->
      <button 
        class="menu-item logout-item"
        @click="handleLogout"
        aria-label="Log Out"
      >
        <div class="menu-content">
          <div class="icon-wrapper logout-icon">
            <md-icon>logout</md-icon>
            <div class="icon-background"></div>
          </div>
          <span class="menu-label">Log out</span>
        </div>
        <span class="menu-ripple"></span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

// Material Web Components
import '@material/web/icon/icon.js';

const router = useRouter();
const emit = defineEmits(['logout']);

function handleEditProfile() {
  router.push('/profile/edit');
}

function handleManageBarcode() {
  router.push('/barcode/dashboard');
}

function handleLogout() {
  emit('logout');
}
</script>

<style scoped>
/* Material Design 3 Menu System */
.menu-container {
  padding: 0;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 0;
}

/* Material 3 Interactive Surface */
.menu-item {
  position: relative;
  background: transparent;
  border: none;
  padding: 16px 8px;
  border-radius: var(--md-sys-shape-corner-large);
  cursor: pointer;
  transition: all 0.2s var(--md-sys-motion-easing-standard);
  overflow: hidden;
  font-family: 'Roboto', sans-serif;
}

/* Hover State */
.menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--md-sys-color-on-surface);
  opacity: 0;
  transition: opacity 0.2s var(--md-sys-motion-easing-standard);
  pointer-events: none;
}

.menu-item:hover::before {
  opacity: 0.08;
}

.menu-item:focus-visible {
  outline: 2px solid var(--md-sys-color-primary);
  outline-offset: 2px;
}

.menu-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

/* Icon System - Material 3 */
.icon-wrapper {
  position: relative;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s var(--md-sys-motion-easing-standard);
}

.icon-background {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: var(--md-sys-color-primary-container);
  transform: translate(-50%, -50%);
  transition: all 0.3s var(--md-sys-motion-easing-standard);
}

.icon-wrapper md-icon {
  font-size: 28px;
  color: var(--md-sys-color-on-primary-container);
  position: relative;
  z-index: 1;
  transition: all 0.3s var(--md-sys-motion-easing-standard);
}

/* Hover Effects */
.menu-item:hover .icon-wrapper {
  transform: translateY(-4px);
}

.menu-item:hover .icon-background {
  background: var(--md-sys-color-primary);
  box-shadow: var(--md-sys-elevation-level2);
}

.menu-item:hover .icon-wrapper md-icon {
  color: var(--md-sys-color-on-primary);
  transform: scale(1.1);
}

/* Active State */
.menu-item:active .icon-wrapper {
  transform: translateY(-2px);
}

.menu-item:active .icon-background {
  transform: translate(-50%, -50%) scale(0.95);
}

/* Logout Specific Styling */
.logout-icon .icon-background {
  background: var(--md-sys-color-error-container);
}

.logout-icon md-icon {
  color: var(--md-sys-color-on-error-container);
}

.logout-item:hover .logout-icon .icon-background {
  background: var(--md-sys-color-error);
}

.logout-item:hover .logout-icon md-icon {
  color: var(--md-sys-color-on-error);
}

.logout-item .menu-label {
  color: var(--md-sys-color-error);
}

/* Typography - Material 3 Label */
.menu-label {
  text-align: center;
  color: var(--md-sys-color-on-surface);
  font-size: 12px;
  line-height: 16px;
  font-weight: 500;
  letter-spacing: 0.5px;
  white-space: nowrap;
  transition: color 0.2s var(--md-sys-motion-easing-standard);
}

.menu-item:hover .menu-label {
  color: var(--md-sys-color-primary);
}

.logout-item:hover .menu-label {
  color: var(--md-sys-color-error);
}

/* Ripple Effect */
.menu-ripple {
  position: absolute;
  border-radius: 50%;
  background: currentColor;
  opacity: 0;
  pointer-events: none;
}

.menu-item:active .menu-ripple {
  width: 100px;
  height: 100px;
  top: 50%;
  left: 50%;
  opacity: 0.12;
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s, opacity 0.6s;
}

/* Touch Target Compliance */
@media (pointer: coarse) {
  .menu-item {
    min-height: 48px;
    min-width: 48px;
  }
}

/* Responsive Layout */
@media (max-width: 600px) {
  .menu-grid {
    gap: 8px;
  }
  
  .menu-item {
    padding: 12px 4px;
  }
  
  .icon-wrapper {
    width: 56px;
    height: 56px;
  }
  
  .icon-wrapper md-icon {
    font-size: 24px;
  }
  
  .menu-label {
    font-size: 11px;
    line-height: 14px;
  }
}

/* Subtle Animation */
@media (prefers-reduced-motion: no-preference) {
  .icon-wrapper {
    animation: subtle-float 4s ease-in-out infinite;
    animation-delay: calc(var(--item-index, 0) * 0.2s);
  }
  
  .menu-item:nth-child(1) .icon-wrapper {
    --item-index: 0;
  }
  
  .menu-item:nth-child(2) .icon-wrapper {
    --item-index: 1;
  }
  
  .menu-item:nth-child(3) .icon-wrapper {
    --item-index: 2;
  }
}

@keyframes subtle-float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

/* Accessibility */
.menu-item:focus-visible .icon-background {
  background: var(--md-sys-color-primary);
}

.menu-item:focus-visible .icon-wrapper md-icon {
  color: var(--md-sys-color-on-primary);
}

@media (prefers-reduced-motion: reduce) {
  .menu-item,
  .icon-wrapper,
  .icon-background,
  .menu-item md-icon {
    transition: none;
    animation: none;
  }
}
</style> 