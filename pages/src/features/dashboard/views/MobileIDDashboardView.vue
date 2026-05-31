<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h3 class="md-typescale-title-medium md-m-0">MobileID Dashboard</h3>
        </div>
        <md-filled-tonal-button @click="router.push('/')">
          <md-icon slot="icon">arrow_back</md-icon>
          Back to Home
        </md-filled-tonal-button>
      </div>
    </header>

    <!-- Flash Messages -->
    <transition name="slide-down">
      <div
        v-if="message"
        :class="[
          'message-toast',
          'md-banner',
          messageType === 'success' ? 'md-banner-success' : 'md-banner-error',
        ]"
      >
        <md-icon>{{ messageType === 'success' ? 'check_circle' : 'error' }}</md-icon>
        <span class="md-typescale-body-medium">{{ message }}</span>
        <md-icon-button @click="message = ''">
          <md-icon>close</md-icon>
        </md-icon-button>
      </div>
    </transition>

    <!-- Main Content -->
    <main class="md-content dashboard-shell">
      <!-- Mobile: compact horizontal tab navigation -->
      <nav class="dashboard-tab-bar" aria-label="Dashboard sections">
        <div v-for="tab in tabs" :key="tab.id" class="chip-wrapper" @click="setTab(tab.id)">
          <md-filter-chip :selected="activeTab === tab.id">
            <md-icon slot="icon">{{ tab.icon }}</md-icon>
            {{ tab.label }}
          </md-filter-chip>
        </div>
      </nav>

      <!-- Desktop: vertical navigation rail -->
      <nav class="dashboard-nav-rail" aria-label="Dashboard sections">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="nav-rail-item"
          :class="{ 'is-active': activeTab === tab.id }"
          :aria-current="activeTab === tab.id ? 'page' : undefined"
          @click="setTab(tab.id)"
        >
          <span class="nav-rail-indicator">
            <md-icon>{{ tab.icon }}</md-icon>
          </span>
          <span class="nav-rail-label md-typescale-label-medium">{{ tab.label }}</span>
        </button>
      </nav>

      <!-- Tab content region -->
      <div class="dashboard-content">
        <!-- Barcode Settings -->
        <SettingsCard
          v-show="activeTab === 'Overview'"
          :associate-user-profile-with-barcode="
            Boolean(settings.associate_user_profile_with_barcode)
          "
          :barcode-choices="barcodeChoices"
          :current-barcode-has-profile="currentBarcodeHasProfile"
          :current-barcode-info="currentBarcodeInfo"
          :errors="errors"
          :format-date="formatDate"
          :format-relative-time="formatRelativeTime"
          :is-dynamic-selected="isDynamicSelected"
          :is-saving="isSaving"
          :pull-settings="pullSettings"
          :selected-barcode="selectedBarcode"
          :settings="settings"
          @update-associate="
            (val) => {
              settings.associate_user_profile_with_barcode = val;
              onSettingChange();
            }
          "
          @update-pull-setting="
            (val) => {
              pullSettings.pull_setting = val;
              onSettingChange();
            }
          "
          @update-gender-setting="
            (val) => {
              pullSettings.gender_setting = val;
              onSettingChange();
            }
          "
        />

        <!-- Camera/Scanner Detection Settings -->
        <CameraSettingsCard
          v-show="activeTab === 'Camera'"
          :scanner-detection-enabled="Boolean(settings.scanner_detection_enabled)"
          :prefer-front-camera="Boolean(settings.prefer_front_camera)"
          :is-saving="isSaving"
          @update-scanner-detection="
            (val) => {
              settings.scanner_detection_enabled = val;
              onSettingChange();
            }
          "
          @update-prefer-front-camera="
            (val) => {
              settings.prefer_front_camera = val;
              onSettingChange();
            }
          "
        />

        <!-- Barcodes List -->
        <BarcodesListCard
          v-show="activeTab === 'Barcodes'"
          :active-tab="activeTab"
          :filter-type="filterType"
          :filtered-barcodes="filteredBarcodes"
          :has-active-filters="hasActiveFilters"
          :owned-only="ownedOnly"
          :pull-settings="pullSettings"
          :settings="settings"
          :updating-limit="updatingLimit"
          @delete="deleteBarcode"
          @update-filter="onFilterChange"
          @toggle-owned="toggleOwned"
          @set-active="setActiveBarcode"
          @toggle-share="toggleShare"
          @update-limit="updateDailyLimit"
          @increment-limit="incrementDailyLimit"
          @decrement-limit="decrementDailyLimit"
          @toggle-unlimited-switch="toggleUnlimitedSwitch"
          @apply-limit-preset="applyLimitPreset"
        />

        <!-- Profile Settings -->
        <ProfileTabCard v-show="activeTab === 'Profile'" />

        <!-- Add Barcode Section -->
        <AddBarcodeCard
          v-show="activeTab === 'Add'"
          :active-tab="activeTab"
          @added="loadDashboard"
          @message="showMessage"
        />

        <!-- Devices Section -->
        <DevicesCard v-show="activeTab === 'Devices'" />

        <!-- Footer -->
        <footer class="dashboard-footer">
          <p class="md-typescale-body-small">
            <router-link to="/privacy" class="privacy-link-text">Privacy Policy</router-link>
          </p>
        </footer>
      </div>
    </main>

    <!-- Delete Confirmation Dialog -->
    <md-dialog :open="showConfirmDialog" @close="showConfirmDialog = false">
      <div slot="headline">Delete Barcode?</div>
      <form slot="content" method="dialog">
        <p class="md-typescale-body-large">
          This will permanently delete the barcode. This action cannot be undone.
        </p>
      </form>
      <div slot="actions">
        <md-text-button @click="showConfirmDialog = false">Cancel</md-text-button>
        <md-filled-button @click="confirmDelete">Delete</md-filled-button>
      </div>
    </md-dialog>
  </div>
</template>

<script setup lang="ts">
import {
  SettingsCard,
  CameraSettingsCard,
  BarcodesListCard,
  AddBarcodeCard,
  DevicesCard,
  ProfileTabCard,
  tabs,
  useBarcodeDashboardViewSetup,
} from './MobileIDDashboardView.setup';

const {
  router,
  formatDate,
  formatRelativeTime,
  message,
  messageType,
  errors,
  isSaving,
  activeTab,
  settings,
  pullSettings,
  barcodeChoices,
  filterType,
  ownedOnly,
  showConfirmDialog,
  isDynamicSelected,
  currentBarcodeHasProfile,
  selectedBarcode,
  filteredBarcodes,
  hasActiveFilters,
  currentBarcodeInfo,
  updatingLimit,
  loadDashboard,
  onSettingChange,
  setActiveBarcode,
  deleteBarcode,
  confirmDelete,
  toggleShare,
  onFilterChange,
  toggleOwned,
  setTab,
  showMessage,
  updateDailyLimit,
  incrementDailyLimit,
  decrementDailyLimit,
  toggleUnlimitedSwitch,
  applyLimitPreset,
} = useBarcodeDashboardViewSetup();
</script>

<style scoped>
/* Responsive shell: desktop navigation rail beside content, mobile tab bar above. */
.dashboard-shell {
  display: grid;
  gap: var(--md-sys-spacing-6);
}

.dashboard-content {
  min-width: 0; /* allow children to shrink instead of overflowing the grid */
}

/* --- Mobile horizontal tab bar (default) --- */
.dashboard-tab-bar {
  display: flex;
  align-items: center;
  gap: var(--md-sys-spacing-2);
  margin-bottom: var(--md-sys-spacing-2);
  overflow-x: auto;
  overflow-y: hidden;
  flex-wrap: nowrap;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.dashboard-tab-bar::-webkit-scrollbar {
  display: none;
}

/* The chip wrapper catches clicks anywhere on the chip. */
.chip-wrapper {
  cursor: pointer;
  flex: 0 0 auto;
}

.chip-wrapper md-filter-chip {
  pointer-events: none;
}

/* Desktop rail hidden on mobile. */
.dashboard-nav-rail {
  display: none;
}

/* --- Desktop navigation rail (>= 905px) --- */
@media (min-width: 905px) {
  .dashboard-shell {
    grid-template-columns: 248px 1fr;
    align-items: start;
  }

  .dashboard-tab-bar {
    display: none;
  }

  .dashboard-nav-rail {
    display: flex;
    flex-direction: column;
    gap: var(--md-sys-spacing-1);
    position: sticky;
    top: var(--md-sys-spacing-6);
    padding: var(--md-sys-spacing-3);
    background: var(--md-sys-color-surface-container-low);
    border-radius: var(--md-sys-shape-corner-large);
    border: 1px solid var(--md-sys-color-outline-variant);
  }

  .nav-rail-item {
    display: flex;
    align-items: center;
    gap: var(--md-sys-spacing-3);
    width: 100%;
    padding: var(--md-sys-spacing-2) var(--md-sys-spacing-3);
    border: none;
    background: transparent;
    border-radius: var(--md-sys-shape-corner-full);
    color: var(--md-sys-color-on-surface-variant);
    font: inherit;
    text-align: left;
    cursor: pointer;
    transition:
      background-color 0.15s ease,
      color 0.15s ease;
  }

  .nav-rail-item:hover {
    background: var(--md-sys-color-surface-container-high);
    color: var(--md-sys-color-on-surface);
  }

  .nav-rail-item:focus-visible {
    outline: 2px solid var(--md-sys-color-primary);
    outline-offset: 2px;
  }

  .nav-rail-indicator {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    width: 40px;
    height: 32px;
    border-radius: var(--md-sys-shape-corner-full);
  }

  .nav-rail-item.is-active {
    color: var(--md-sys-color-on-secondary-container);
  }

  .nav-rail-item.is-active .nav-rail-indicator {
    background: var(--md-sys-color-secondary-container);
  }

  .nav-rail-item.is-active .nav-rail-label {
    font-weight: 600;
  }

  .nav-rail-label {
    flex: 1 1 auto;
  }
}
</style>
