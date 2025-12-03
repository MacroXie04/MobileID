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
    <main class="md-content">
      <!-- Tabs Navigation -->
      <div class="tabs-bar md-flex md-gap-2 md-items-center md-mb-6">
        <div class="chip-wrapper" @click="setTab('Overview')">
          <md-filter-chip :selected="activeTab === 'Overview'">
            <md-icon slot="icon">tune</md-icon>
            Overview
          </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Camera')">
          <md-filter-chip :selected="activeTab === 'Camera'">
            <md-icon slot="icon">sensors</md-icon>
            Scanner Detection
          </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Barcodes')">
          <md-filter-chip :selected="activeTab === 'Barcodes'">
            <md-icon slot="icon">inventory_2</md-icon>
            Available Barcodes
          </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Devices')">
          <md-filter-chip :selected="activeTab === 'Devices'">
            <md-icon slot="icon">devices</md-icon>
            Devices Management
          </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Add')">
          <md-filter-chip :selected="activeTab === 'Add'">
            <md-icon slot="icon">add_circle</md-icon>
            Add Barcode
          </md-filter-chip>
        </div>
      </div>

      <!-- Barcode Settings -->
      <SettingsCard
        v-show="activeTab === 'Overview'"
        :associate-user-profile-with-barcode="Boolean(settings.associate_user_profile_with_barcode)"
        :barcode-choices="barcodeChoices"
        :current-barcode-has-profile="currentBarcodeHasProfile"
        :current-barcode-info="currentBarcodeInfo"
        :errors="errors"
        :format-date="formatDate"
        :format-relative-time="formatRelativeTime"
        :is-dynamic-selected="isDynamicSelected"
        :is-saving="isSaving"
        :is-user-group="isUserGroup"
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
          <a href="/privacy.html" target="_blank" rel="noopener noreferrer" class="privacy-link-text">Privacy Policy</a>
        </p>
      </footer>
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

<script setup>
import {
  SettingsCard,
  CameraSettingsCard,
  BarcodesListCard,
  AddBarcodeCard,
  DevicesCard,
  useBarcodeDashboardViewSetup,
} from './BarcodeDashboardView.setup.js';

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
  isUserGroup,
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
