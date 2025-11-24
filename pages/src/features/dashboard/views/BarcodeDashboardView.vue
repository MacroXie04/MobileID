<template>
  <div class="md-layout-container">
    <!-- Header Section -->
    <header class="md-top-app-bar">
      <div class="md-top-app-bar-content">
        <div class="header-title">
          <h3 class="md-typescale-title-medium md-m-0">Barcode Dashboard</h3>
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
          <md-filter-chip :selected="activeTab === 'Overview'"> Overview </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Barcodes')">
          <md-filter-chip :selected="activeTab === 'Barcodes'"> Available Barcodes </md-filter-chip>
        </div>
        <div class="chip-wrapper" @click="setTab('Add')">
          <md-filter-chip :selected="activeTab === 'Add'"> Transfer & Add Barcode </md-filter-chip>
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
        :server-verification="Boolean(settings.server_verification)"
        :settings="settings"
        @update-associate="
          (val) => {
            settings.associate_user_profile_with_barcode = val;
            onSettingChange();
          }
        "
        @update-server="
          (val) => {
            settings.server_verification = val;
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
      <!-- Floating Action Button to Add -->
      <md-fab style="position: fixed; right: 24px; bottom: 24px; z-index: 10" @click="goToAddTab">
        <md-icon slot="icon">add</md-icon>
        <div slot="label">Add Barcode</div>
      </md-fab>
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
import { useRouter } from 'vue-router';
import { formatDate, formatRelativeTime } from '@shared/utils/common/dateUtils';
import SettingsCard from '@dashboard/components/SettingsCard.vue';
import BarcodesListCard from '@dashboard/components/BarcodesListCard.vue';
import AddBarcodeCard from '@dashboard/components/AddBarcodeCard.vue';
import { useDashboardLogic } from '@dashboard/composables/useDashboardLogic.js';
import '@/assets/styles/dashboard/BarcodeDashboard.css';

// Router
const router = useRouter();

const {
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
  
  // Computed
  isDynamicSelected,
  currentBarcodeHasProfile,
  selectedBarcode,
  filteredBarcodes,
  hasActiveFilters,
  currentBarcodeInfo,
  updatingLimit,

  // Methods
  loadDashboard,
  onSettingChange,
  setActiveBarcode,
  deleteBarcode,
  confirmDelete,
  toggleShare,
  onFilterChange,
  toggleOwned,
  goToAddTab,
  setTab,
  showMessage,
  
  // Daily Limit methods
  updateDailyLimit,
  incrementDailyLimit,
  decrementDailyLimit,
  toggleUnlimitedSwitch,
  applyLimitPreset
} = useDashboardLogic();
</script>
