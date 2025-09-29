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
      <div v-if="message" :class="['message-toast', 'md-banner', messageType === 'success' ? 'md-banner-success' : 'md-banner-error']">
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
        <md-filter-chip :selected="activeTab === 'Overview'" @click="activeTab = 'Overview'">
          Overview
        </md-filter-chip>
        <md-filter-chip :selected="activeTab === 'Barcodes'" @click="activeTab = 'Barcodes'">
          My Barcodes
        </md-filter-chip>
        <md-filter-chip :selected="activeTab === 'Add'" @click="activeTab = 'Add'">
          Add
        </md-filter-chip>
      </div>
      <!-- Transfer Barcode Section -->
      <section v-if="activeTab === 'Overview'" class="md-card md-mb-6">
        <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
          <md-icon>cookie</md-icon>
          <h2 class="md-typescale-headline-small md-m-0">Transfer Barcode</h2>
          <transition name="fade">
            <div v-if="transferLoading" class="save-indicator md-flex md-items-center md-gap-2 md-ml-auto">
              <md-circular-progress indeterminate></md-circular-progress>
              <span class="md-typescale-body-small">Collecting Data from URL...</span>
            </div>
          </transition>
        </div>

        <div class="settings-content md-flex md-flex-column md-gap-4">
          <md-outlined-text-field
            v-model="transferCookie"
            :error="!!transferErrors.cookie"
            :error-text="transferErrors.cookie"
            label="Barcode Cookie"
            placeholder="Paste your Barcode cookies here"
            @input="clearTransferError('cookie')"
          >
            <md-icon slot="leading-icon">cookie</md-icon>
          </md-outlined-text-field>

          <div class="md-flex md-items-center md-gap-2">
            <md-icon>link</md-icon>
            <span class="md-typescale-body-medium">ID Server:</span>
            <code class="md-typescale-body-medium">https://icatcard.ucmerced.edu/mobileid/</code>
          </div>

          <div class="form-actions md-flex md-gap-3 md-flex-wrap">
            <md-filled-button @click="requestTransferCode" :disabled="transferLoading || !transferCookie.trim()">
              <md-icon slot="icon">sync_alt</md-icon>
              Request Transfer
            </md-filled-button>
          </div>

          <transition name="fade">
            <div v-if="transferSuccess" class="md-banner md-banner-success">
              <md-icon>check_circle</md-icon>
              <span class="md-typescale-body-medium">
                {{ transferSuccessMessage || 'Barcode data stored successfully!' }}
              </span>
            </div>
          </transition>

          <transition name="fade">
            <div v-if="transferError" class="md-banner md-banner-error">
              <md-icon>error</md-icon>
              <span class="md-typescale-body-medium">{{ transferError }}</span>
            </div>
          </transition>
        </div>
      </section>
      <!-- Settings Card -->
      <section v-if="activeTab === 'Overview'" class="settings-card md-card md-mb-6">
        <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
          <div class="header-icon-wrapper">
            <md-icon>tune</md-icon>
          </div>
          <h2 class="md-typescale-headline-small md-m-0">Barcode Settings</h2>
          <transition name="fade">
            <div v-if="isSaving" class="save-indicator md-flex md-items-center md-gap-2 md-ml-auto">
              <md-circular-progress indeterminate></md-circular-progress>
              <span class="md-typescale-body-small">Saving...</span>
            </div>
          </transition>
        </div>

        <div class="settings-content">
          <!-- Active Barcode Display -->
          <transition name="scale-fade">
            <div v-if="currentBarcodeInfo" class="active-barcode-card md-mb-6">
              <div class="active-barcode-header">
                <md-icon class="active-icon pulse">verified</md-icon>
                <span class="md-typescale-label-medium">CURRENTLY ACTIVE</span>
              </div>
              <div class="active-barcode-info">
                <div class="barcode-type-badge">
                  <md-icon>
                    {{ settings.barcode && barcodeChoices.find(c => Number(c.id) === Number(settings.barcode))?.barcode_type === 'DynamicBarcode' ? 'qr_code_2' : 
                       settings.barcode && barcodeChoices.find(c => Number(c.id) === Number(settings.barcode))?.barcode_type === 'Identification' ? 'badge' : 'barcode' }}
                  </md-icon>
                </div>
                <div class="barcode-details">
                  <h3 class="md-typescale-title-medium md-m-0">{{ currentBarcodeInfo }}</h3>
                  <p v-if="selectedBarcode && selectedBarcode.barcode_type !== 'Identification'" class="md-typescale-body-small md-m-0 md-mt-1">
                    {{ selectedBarcode.usage_count || 0 }} total scans
                    <span v-if="selectedBarcode.last_used">• Last used {{ formatRelativeTime(selectedBarcode.last_used) }}</span>
                  </p>
                </div>
              </div>
            </div>
          </transition>

          <!-- Usage Statistics Card (hide for Identification) -->
          <div v-if="selectedBarcode && selectedBarcode.barcode_type !== 'Identification' && selectedBarcode.usage_count > 0" class="usage-stats-card md-mb-6">
            <div class="stats-header md-mb-4">
              <md-icon>insights</md-icon>
              <h3 class="md-typescale-title-small md-m-0">Usage Statistics</h3>
            </div>
            
            <div class="stats-grid md-grid-cols-3 md-gap-4 md-mb-4">
              <div class="stat-card">
                <md-icon>trending_up</md-icon>
                <div class="stat-value">{{ selectedBarcode.usage_count || 0 }}</div>
                <div class="stat-label">Total Scans</div>
              </div>
              <div class="stat-card" v-if="selectedBarcode.usage_stats">
                <md-icon>today</md-icon>
                <div class="stat-value">{{ selectedBarcode.usage_stats.daily_used || 0 }}</div>
                <div class="stat-label">Today's Scans</div>
              </div>
              <div class="stat-card" v-if="selectedBarcode.usage_stats && selectedBarcode.usage_stats.daily_limit > 0">
                <md-icon>event_available</md-icon>
                <div class="stat-value">{{ selectedBarcode.usage_stats.daily_remaining || 0 }}</div>
                <div class="stat-label">Remaining Today</div>
              </div>
            </div>

            <div class="recent-activity">
              <h4 class="md-typescale-label-large md-mb-3">Recent Activity</h4>
              <div v-if="selectedBarcode.recent_transactions && selectedBarcode.recent_transactions.length > 0" class="activity-list">
                <div v-for="tx in selectedBarcode.recent_transactions" :key="tx.id" class="activity-item">
                  <div class="activity-icon">
                    <md-icon>person</md-icon>
                  </div>
                  <div class="activity-details">
                    <span class="md-typescale-body-medium">{{ tx.user || 'Unknown User' }}</span>
                    <span class="md-typescale-body-small">{{ formatDate(tx.time_created) }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="empty-activity">
                <md-icon>history_toggle_off</md-icon>
                <span class="md-typescale-body-medium">No recent activity</span>
              </div>
            </div>
          </div>

          <!-- Settings available only for barcodes with profile -->
          <div v-if="isDynamicSelected && currentBarcodeHasProfile" class="settings-grid md-flex md-flex-column md-gap-4">
            <div class="md-typescale-title-small md-muted">Profile & Verification</div>
            <md-list>
              <md-list-item>
                <md-icon slot="start">person_pin</md-icon>
                <div slot="headline">Profile Association</div>
                <div slot="supporting-text">Use profile data from the ID server</div>
                <md-switch
                  slot="end"
                  :selected="Boolean(settings.associate_user_profile_with_barcode)"
                  :disabled="isUserGroup"
                  @change="(e) => { settings.associate_user_profile_with_barcode = e.target.selected; onSettingChange(); }"
                ></md-switch>
              </md-list-item>

              <md-divider inset></md-divider>

              <md-list-item>
                <md-icon slot="start">security</md-icon>
                <div slot="headline">Server Verification</div>
                <div slot="supporting-text">Validate on server (may take longer or fail)</div>
                <md-switch
                  slot="end"
                  :selected="Boolean(settings.server_verification)"
                  @change="(e) => { settings.server_verification = e.target.selected; onSettingChange(); }"
                ></md-switch>
              </md-list-item>
            </md-list>
          </div>

          <!-- Info message when dynamic barcode is selected but has no profile -->
          <div v-if="isDynamicSelected && !currentBarcodeHasProfile" class="info-banner md-mt-4">
            <md-icon>info</md-icon>
            <div class="info-content">
              <h4 class="md-typescale-label-large md-m-0">Profile Settings Unavailable</h4>
              <p class="md-typescale-body-medium md-m-0 md-mt-1">
                Profile settings are only available for barcodes with attached profile data. 
                Transfer a barcode with profile information to access these settings.
              </p>
            </div>
          </div>
          
          <!-- Empty state when no barcode selected -->
          <div v-if="!currentBarcodeInfo" class="empty-settings">
            <md-icon>qr_code_scanner</md-icon>
            <h3 class="md-typescale-headline-small">No Barcode Selected</h3>
            <p class="md-typescale-body-medium">Select a barcode from the list below to view settings and statistics</p>
          </div>

          <div v-if="Object.keys(errors).length > 0" class="md-banner md-banner-error md-mt-4">
            <md-icon>error</md-icon>
            <div class="error-messages">
              <p v-for="(error, field) in errors" :key="field" class="md-typescale-body-medium md-m-0">
                {{ error }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Barcodes List -->
      <section v-if="activeTab === 'Barcodes'" class="md-card md-mb-6">
        <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
          <md-icon>inventory_2</md-icon>
          <h2 class="md-typescale-headline-small md-m-0">My Barcodes</h2>
        </div>

        <!-- Filter Bar -->
        <div class="filter-bar md-flex md-gap-3 md-items-center md-mb-6 md-flex-wrap">
          <div class="filter-controls md-flex md-items-center md-gap-2">
            <md-filter-chip
              :selected="filterType === 'All'"
              @click="filterType = 'All'; onFilterChange()"
            >
              All
            </md-filter-chip>
            <md-filter-chip
              :selected="filterType === 'Dynamic'"
              @click="filterType = 'Dynamic'; onFilterChange()"
            >
              Dynamic
            </md-filter-chip>
            <md-filter-chip
              :selected="filterType === 'Static'"
              @click="filterType = 'Static'; onFilterChange()"
            >
              Static
            </md-filter-chip>
            <md-filter-chip
              :selected="filterType === 'Identification'"
              @click="filterType = 'Identification'; onFilterChange()"
            >
              Identification
            </md-filter-chip>
            
            <md-divider vertical></md-divider>
            
            <md-filter-chip
              :selected="ownedOnly"
              @click="ownedOnly = !ownedOnly; onFilterChange()"
            >
              <md-icon slot="icon">person</md-icon>
              Owned only
            </md-filter-chip>
          </div>
        </div>

        <!-- Barcodes Grid -->
        <transition-group
          v-if="filteredBarcodes.length > 0"
          name="list"
          tag="div"
          class="barcodes-grid md-grid-container md-gap-4"
        >
          <article
            v-for="barcode in filteredBarcodes"
            :key="barcode.id"
            class="barcode-item md-card md-p-5 md-flex md-items-center md-gap-4"
            :class="{
              'is-active': Number(settings.barcode) === Number(barcode.id),
              'is-shared': !barcode.is_owned_by_current_user
            }"
          >
            <!-- Barcode Type Icon -->
            <div class="barcode-type-icon md-flex md-items-center md-justify-center md-rounded-lg">
              <md-icon>
                {{ barcode.barcode_type === 'DynamicBarcode' ? 'qr_code_2' : barcode.barcode_type === 'Identification' ? 'badge' : 'barcode' }}
              </md-icon>
            </div>

            <!-- Barcode Content -->
            <div class="barcode-content">
              <div class="barcode-title-row">
                <h3 class="md-typescale-title-medium md-m-0">
                  {{ getBarcodeDisplayTitle(barcode.barcode_type) }}
                </h3>
                <div class="barcode-badges md-flex md-gap-2 md-flex-wrap">
                  <md-assist-chip>
                    <md-icon slot="icon">
                      {{ barcode.barcode_type === 'DynamicBarcode' ? 'qr_code_2' : barcode.barcode_type === 'Identification' ? 'badge' : 'barcode' }}
                    </md-icon>
                    {{ getBarcodeTypeLabel(barcode.barcode_type) }}
                  </md-assist-chip>
                  <md-assist-chip
                    v-if="Number(settings.barcode) === Number(barcode.id)"
                    aria-label="Active barcode"
                  >
                    <md-icon slot="icon">check_circle</md-icon>
                    Active
                  </md-assist-chip>
                  <md-assist-chip
                    v-if="barcode.owner"
                    aria-label="Owner"
                  >
                    <md-icon slot="icon">person</md-icon>
                    {{ barcode.owner }}
                  </md-assist-chip>
                  <md-assist-chip
                    v-if="!barcode.is_owned_by_current_user"
                    aria-label="Shared barcode"
                  >
                    <md-icon slot="icon">group</md-icon>
                    Shared
                  </md-assist-chip>
                  <md-assist-chip
                    v-if="barcode.barcode_type === 'DynamicBarcode' && barcode.has_profile_addon"
                    :title="getProfileTooltip(barcode)"
                  >
                    <md-icon slot="icon">{{ barcode.profile_info?.has_avatar ? 'account_circle' : 'badge' }}</md-icon>
                    {{ getProfileLabel(barcode) }}
                  </md-assist-chip>
                </div>
              </div>

              <p class="barcode-id md-typescale-body-medium md-mt-2 md-mb-0">
                {{ getBarcodeDisplayId(barcode) }}
                <span v-if="!barcode.is_owned_by_current_user && !barcode.owner" class="owner-label">
                  by {{ barcode.owner }}
                </span>
              </p>

              <div v-if="barcode.barcode_type !== 'Identification' && barcode.usage_count > 0" class="barcode-stats md-flex md-gap-4 md-flex-wrap md-mt-3">
                <span class="stat md-flex md-items-center md-gap-1">
                  <md-icon>trending_up</md-icon>
                  {{ barcode.usage_count }} scan{{ barcode.usage_count !== 1 ? 's' : '' }}
                </span>
                <span v-if="barcode.last_used" class="stat md-flex md-items-center md-gap-1">
                  <md-icon>schedule</md-icon>
                  {{ formatRelativeTime(barcode.last_used) }}
                </span>
                <span v-if="barcode.usage_stats" class="stat md-flex md-items-center md-gap-1">
                  <md-icon>today</md-icon>
                  {{ barcode.usage_stats.daily_used }} today
                  <span v-if="barcode.usage_stats.daily_limit > 0">/ {{ barcode.usage_stats.daily_limit }}</span>
                </span>
              </div>
            </div>

            <!-- Barcode Actions -->
          <div class="barcode-actions md-flex md-items-center md-gap-2">
              <md-filled-tonal-button
                v-if="Number(settings.barcode) !== Number(barcode.id)"
                @click="setActiveBarcode(barcode)"
              >
                <md-icon slot="icon">check_circle</md-icon>
                Set Active
              </md-filled-tonal-button>
              
            <md-assist-chip v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
                             :selected="!!barcode.share_with_others"
                             @click="toggleShare(barcode)"
                             aria-label="Share with others">
              <md-icon slot="icon">{{ barcode.share_with_others ? 'share' : 'lock' }}</md-icon>
              {{ barcode.share_with_others ? 'Shared' : 'Private' }}
            </md-assist-chip>

              <md-icon-button
                v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
                @click="deleteBarcode(barcode)"
              >
                <md-icon>delete</md-icon>
              </md-icon-button>
            </div>

            <!-- Daily Limit Controls for Owned Barcodes (except Identification) -->
            <div v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'" class="barcode-limit-controls md-mt-3">
              <div class="limit-header md-flex md-items-center md-gap-3">
                <div class="limit-header-left md-flex md-items-center md-gap-2">
                  <md-icon class="limit-icon">event</md-icon>
                  <div>
                    <div class="md-typescale-label-large">Daily Limit</div>
                    <div class="md-typescale-body-small md-text-on-surface-variant">Set maximum scans per day</div>
                  </div>
                </div>
                <div class="md-ml-auto md-flex md-items-center md-gap-2">
                  <span class="md-typescale-label-small">Unlimited</span>
                  <md-switch :selected="Number(barcode.daily_usage_limit || 0) === 0" @change="(e) => toggleUnlimitedSwitch(barcode, e)"></md-switch>
                </div>
              </div>

              <div class="limit-controls md-flex md-items-center md-gap-2 md-mt-3">
                <md-icon-button :disabled="Number(barcode.daily_usage_limit || 0) === 0" @click="decrementDailyLimit(barcode)" aria-label="Decrease daily limit">
                  <md-icon>remove</md-icon>
                </md-icon-button>

                <md-outlined-text-field
                  :value="barcode.daily_usage_limit || 0"
                  @input="(e) => updateDailyLimit(barcode, e.target.value)"
                  :disabled="Number(barcode.daily_usage_limit || 0) === 0"
                  type="number"
                  min="0"
                  label="Daily Limit"
                  class="limit-input"
                >
                  <md-icon slot="leading-icon">pin</md-icon>
                </md-outlined-text-field>

                <md-icon-button :disabled="Number(barcode.daily_usage_limit || 0) === 0" @click="incrementDailyLimit(barcode)" aria-label="Increase daily limit">
                  <md-icon>add</md-icon>
                </md-icon-button>

                <div class="limit-presets md-flex md-items-center md-gap-1 md-ml-2">
                  <md-assist-chip @click="applyLimitPreset(barcode, 5)">5</md-assist-chip>
                  <md-assist-chip @click="applyLimitPreset(barcode, 10)">10</md-assist-chip>
                  <md-assist-chip @click="applyLimitPreset(barcode, 20)">20</md-assist-chip>
                </div>

                <md-circular-progress v-if="updatingLimit[barcode.id]" indeterminate></md-circular-progress>
              </div>

              <div class="limit-support md-typescale-body-small md-text-on-surface-variant md-mt-2">0 = unlimited</div>
            </div>
          </article>
        </transition-group>

        <!-- Empty State -->
        <div v-else class="md-empty-state empty-state-box">
          <md-icon class="md-empty-state-icon">qr_code_scanner</md-icon>
          <h3 class="md-typescale-headline-small md-mb-2">
            {{ hasActiveFilters ? 'No barcodes match your filters' : 'No barcodes found' }}
          </h3>
          <p class="md-typescale-body-medium md-m-0">
            {{ hasActiveFilters ? 'Try clearing filters or selecting a different type.' : 'Add your first barcode to get started.' }}
          </p>
        </div>
      </section>

      <!-- Add Barcode Section -->
      <section v-if="activeTab === 'Add'" ref="addSection" class="md-card">
        <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
          <md-icon>add_circle</md-icon>
          <h2 class="md-typescale-headline-small md-m-0">Add New Barcode</h2>
        </div>

        <form class="md-form" @submit.prevent="addBarcode">
          <div class="form-content md-flex md-flex-column md-gap-4">
            <md-outlined-text-field
              v-model="newBarcode"
              :error="!!errors.newBarcode"
              :error-text="errors.newBarcode"
              label="Barcode Number"
              placeholder="Enter or scan barcode"
              @input="clearError('newBarcode')"
            >
              <md-icon slot="leading-icon">pin</md-icon>
            </md-outlined-text-field>

            <div class="form-actions md-flex md-gap-3 md-flex-wrap">
              <md-outlined-button
                type="button"
                @click="toggleScanner"
              >
                <md-icon slot="icon">
                  {{ showScanner ? 'videocam_off' : 'qr_code_scanner' }}
                </md-icon>
                {{ showScanner ? 'Close Scanner' : 'Scan with Camera' }}
              </md-outlined-button>

              <md-filled-button type="submit" :disabled="!newBarcode.trim()">
                <md-icon slot="icon">add</md-icon>
                Add Barcode
              </md-filled-button>
            </div>
          </div>

          <!-- Scanner Section -->
          <transition name="expand">
            <div v-if="showScanner" class="scanner-container md-card md-card-filled md-rounded-lg md-p-5 md-mt-6">
              <div class="scanner-header md-flex md-items-center md-gap-3 md-mb-4">
                <md-icon>camera</md-icon>
                <span class="md-typescale-title-medium">Barcode Scanner</span>
                <md-outlined-select
                  v-if="cameras.length > 1"
                  v-model="selectedCameraId"
                  class="camera-select md-ml-auto"
                >
                  <md-select-option
                    v-for="device in cameras"
                    :key="device.deviceId"
                    :value="device.deviceId"
                  >
                    <div slot="headline">{{ device.label }}</div>
                  </md-select-option>
                </md-outlined-select>
              </div>

              <div class="scanner-viewport md-rounded-lg">
                <video
                  ref="videoRef"
                  autoplay
                  muted
                  playsinline
                  webkit-playsinline
                ></video>
                <div class="scanner-overlay">
                  <div class="scanner-frame"></div>
                </div>
              </div>

              <div class="scanner-status md-text-center md-mt-4">
                <md-linear-progress v-if="scanning" indeterminate></md-linear-progress>
                <p class="md-typescale-body-small md-mt-2">{{ scannerStatus }}</p>
              </div>
            </div>
          </transition>
        </form>
      </section>
      <!-- Floating Action Button to Add -->
      <md-fab style="position: fixed; right: 24px; bottom: 24px; z-index: 10;" @click="goToAddTab">
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
import {nextTick, onMounted, onUnmounted, ref, watch, computed} from 'vue';
import {useRouter} from 'vue-router';
import {useApi} from '@/composables/useApi';
import '@/assets/css/BarcodeDashboard.css';

// Router
const router = useRouter();

// API composable
const {
  apiGetBarcodeDashboard,
  apiUpdateBarcodeSettings,
  apiCreateBarcode,
  apiDeleteBarcode,
  apiTransferCatCard,
  apiGetActiveProfile,
  apiUpdateBarcodeShare,
  apiUpdateBarcodeDailyLimit
} = useApi();

// Reactive state
const loading = ref(true);
const message = ref('');
const messageType = ref('success');
const errors = ref({});
const isSaving = ref(false);

// Tabs
const activeTab = ref('Overview');

// Dashboard data
const settings = ref({
  associate_user_profile_with_barcode: false,
  server_verification: false,
  barcode: null
});
const barcodes = ref([]);
const barcodeChoices = ref([]);
const isUserGroup = ref(false);
const isSchoolGroup = ref(false);
const isDynamicSelected = computed(() => {
  if (!settings.value.barcode) return false;
  const current = barcodeChoices.value.find(c => Number(c.id) === Number(settings.value.barcode));
  return current?.barcode_type === 'DynamicBarcode';
});

const currentBarcodeHasProfile = computed(() => {
  if (!settings.value.barcode) return false;
  const current = barcodeChoices.value.find(c => Number(c.id) === Number(settings.value.barcode));
  return current?.has_profile_addon || false;
});

// Selected barcode full object (from barcodes list)
const selectedBarcode = computed(() => {
  if (!settings.value.barcode) return null;
  const id = Number(settings.value.barcode);
  return (barcodes.value || []).find(b => Number(b.id) === id) || null;
});

// Form data
const newBarcode = ref('');

// Scanner state
const showScanner = ref(false);
const scanning = ref(false);
const scannerStatus = ref('Position the barcode within the camera view');
const videoRef = ref(null);
let codeReader = null;
const cameras = ref([]);
const selectedCameraId = ref(null);
const hasCameraPermission = ref(false);

// Per-barcode daily limit updating state
const updatingLimit = ref({});

// Dialog state
const showConfirmDialog = ref(false);
const barcodeToDelete = ref(null);

// Template refs
const addSection = ref(null);

// Clear specific error
const clearError = (field) => {
  delete errors.value[field];
};

// Transfer CatCard state
const transferCookie = ref('');
const transferLoading = ref(false);
const transferSuccess = ref(false);
const transferSuccessMessage = ref('');
const transferError = ref('');
const transferErrors = ref({});

function clearTransferError(field) {
  delete transferErrors.value[field];
  transferError.value = '';
  transferSuccess.value = false;
  transferSuccessMessage.value = '';
}

async function requestTransferCode() {
  try {
    transferError.value = '';
    transferSuccess.value = false;
    transferSuccessMessage.value = '';
    transferErrors.value = {};

    if (!transferCookie.value || !transferCookie.value.trim()) {
      transferErrors.value.cookie = 'Cookie is required';
      return;
    }

    transferLoading.value = true;

    const data = await apiTransferCatCard(transferCookie.value);

    if (data && data.success) {
      transferSuccess.value = true;
      transferSuccessMessage.value = data.message || 'Barcode data stored successfully!';
      // Clear the cookie field on success
      transferCookie.value = '';
      // Reload dashboard to show any new barcode data
      setTimeout(() => {
        loadDashboard();
      }, 1000);
    } else {
      transferError.value = data.error || 'Transfer failed.';
    }
  } catch (error) {
    if (error.status === 400 && error.errors) {
      // Handle validation errors from API
      transferError.value = error.message || 'Invalid request';
    } else {
      transferError.value = error.message || 'Network error occurred';
    }
  } finally {
    transferLoading.value = false;
  }
}

// Load dashboard data
async function loadDashboard() {
  try {
    loading.value = true;
    const data = await apiGetBarcodeDashboard();

    // Clear previous state
    settings.value = {
      associate_user_profile_with_barcode: false,
      server_verification: false,
      barcode: null
    };
    barcodeChoices.value = [];

    // Set choices first
    barcodeChoices.value = data.settings.barcode_choices || [];

    // Then set settings with proper type conversion
    await nextTick(); // Wait for choices to be rendered

    settings.value = {
      associate_user_profile_with_barcode: Boolean(data.settings.associate_user_profile_with_barcode),
      server_verification: Boolean(data.settings.server_verification),
      barcode: data.settings.barcode ? Number(data.settings.barcode) : null
    };

    barcodes.value = data.barcodes || [];
    isUserGroup.value = Boolean(data.is_user_group);
    isSchoolGroup.value = Boolean(data.is_school_group);

    // Check for active profile (for School users with barcode profile association)
    await checkActiveProfile();

  } catch (error) {
    showMessage('Failed to load dashboard: ' + error.message, 'danger');
  } finally {
    loading.value = false;
  }
}

// Check and apply active profile
async function checkActiveProfile() {
  try {
    console.log('Dashboard: Checking active profile...');
    const response = await apiGetActiveProfile();
    console.log('Dashboard: Active profile response:', response);
    
    if (response && response.profile_info) {
      console.log('Dashboard: Active profile found, updating page title and info');
      // Show a brief notification about active profile association
      showMessage(`Profile Association Active: ${response.profile_info.name}`, 'success');
    } else {
      console.log('Dashboard: No active profile association');
    }
  } catch (error) {
    console.error('Dashboard: Failed to check active profile:', error);
  }
}

// Auto-save settings with debounce
let saveTimeout = null;

async function autoSaveSettings() {
  // Record start time for minimum display duration
  const startTime = Date.now();

  try {
    isSaving.value = true;
    errors.value = {};

    // ensure barcode ID is a number
    const settingsToSend = {
      ...settings.value,
      barcode: settings.value.barcode ? Number(settings.value.barcode) : null
    };

    const response = await apiUpdateBarcodeSettings(settingsToSend);

    if (response.status === 'success') {
      // update choices from response
      if (response.settings && response.settings.barcode_choices) {
        barcodeChoices.value = response.settings.barcode_choices;
      }
      // Ensure the updated barcode value is properly typed
      if (response.settings && response.settings.barcode !== undefined) {
        settings.value.barcode = response.settings.barcode ? Number(response.settings.barcode) : null;
      }
      // Update association status from backend
      if (response.settings && response.settings.associate_user_profile_with_barcode !== undefined) {
        settings.value.associate_user_profile_with_barcode = Boolean(response.settings.associate_user_profile_with_barcode);
      }
    }

    // Ensure minimum display time of 1 second
    const elapsed = Date.now() - startTime;
    const remainingTime = Math.max(0, 1000 - elapsed);

    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime));
    }

  } catch (error) {
    if (error.status === 400 && error.errors) {
      errors.value = error.errors;
    } else {
      showMessage('Failed to save settings: ' + error.message, 'danger');
    }

    // Also ensure minimum display time for errors
    const elapsed = Date.now() - startTime;
    const remainingTime = Math.max(0, 1000 - elapsed);

    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime));
    }
  } finally {
    isSaving.value = false;
  }
}

// Deprecated - kept for backward compatibility
async function updateSettings() {
  await autoSaveSettings();
}

// Filter/sort state and helpers
const searchQuery = ref('');
const filterType = ref('All'); // All | Dynamic | Static | Identification
const sortBy = ref('Newest'); // Newest | Oldest | MostUsed
const ownedOnly = ref(false);

function normalize(str) {
  try { return String(str || '').toLowerCase(); } catch { return ''; }
}

const filteredBarcodes = computed(() => {
  let result = [...(barcodes.value || [])];

  if (ownedOnly.value) {
    result = result.filter(b => b.is_owned_by_current_user);
  }

  if (filterType.value !== 'All') {
    if (filterType.value === 'Dynamic') {
      result = result.filter(b => b.barcode_type === 'DynamicBarcode');
    } else if (filterType.value === 'Static') {
      result = result.filter(b => b.barcode_type === 'Others');
    } else if (filterType.value === 'Identification') {
      result = result.filter(b => b.barcode_type === 'Identification');
    }
  }

  // removed search and sort controls; keep default ordering from API

  return result;
});

function onFilterChange() {
  // Computed handles updates. This is here for explicit @change bindings.
}

const hasActiveFilters = computed(() => {
  return filterType.value !== 'All' || ownedOnly.value;
});

function resetFilters() {
  filterType.value = 'All';
  ownedOnly.value = false;
}

// Add new barcode
async function addBarcode() {
  try {
    errors.value = {};

    if (!newBarcode.value.trim()) {
      errors.value.newBarcode = 'Barcode is required';
      return;
    }

    const response = await apiCreateBarcode(newBarcode.value);

    if (response.status === 'success') {
      showMessage(response.message, 'success');
      newBarcode.value = '';
      // Reload dashboard to get updated data
      await loadDashboard();
    }
  } catch (error) {
    if (error.status === 400 && error.errors) {
      // Handle validation errors from API
      if (error.errors.barcode && error.errors.barcode.length > 0) {
        errors.value.newBarcode = error.errors.barcode[0];
      } else if (error.status === 400 && error.message && error.message.includes('barcode with this barcode already exists')) {
        errors.value.newBarcode = 'Barcode already exists';
      } else {
        errors.value.newBarcode = 'Invalid barcode';
      }
    } else {
      showMessage('Failed to add barcode', 'danger');
    }
  }
}

// Delete barcode
async function deleteBarcode(barcode) {
  // Guard: only allow deletion for barcodes owned by the current user
  if (!barcode || !barcode.is_owned_by_current_user) {
    showMessage('You can only delete your own barcode', 'danger');
    return;
  }
  barcodeToDelete.value = barcode.id;
  showConfirmDialog.value = true;
}

async function confirmDelete() {
  if (!barcodeToDelete.value) return;

  try {
    const response = await apiDeleteBarcode(barcodeToDelete.value);

    if (response.status === 'success') {
      showMessage(response.message, 'success');
      // Reload dashboard to get updated data
      await loadDashboard();
    }
  } catch (error) {
    showMessage('Failed to delete barcode: ' + error.message, 'danger');
  } finally {
    showConfirmDialog.value = false;
    barcodeToDelete.value = null;
  }
}

// Toggle share_with_others for an owned barcode
async function toggleShare(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  try {
    const next = !barcode.share_with_others;
    const res = await apiUpdateBarcodeShare(barcode.id, next);
    if (res?.status === 'success' && res?.barcode) {
      // Update local list entry optimistically with server echo
      const idx = barcodes.value.findIndex(b => Number(b.id) === Number(barcode.id));
      if (idx !== -1) {
        barcodes.value[idx] = { ...barcodes.value[idx], share_with_others: res.barcode.share_with_others };
      }
      showMessage(next ? 'Sharing enabled' : 'Sharing disabled', 'success');
    }
  } catch (e) {
    showMessage('Failed to update sharing: ' + (e?.message || 'Unknown error'), 'danger');
  }
}

// Update daily usage limit with debounce
let dailyLimitTimeout = null;
async function updateDailyLimit(barcode, value) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  
  // Clear previous timeout
  if (dailyLimitTimeout) {
    clearTimeout(dailyLimitTimeout);
  }
  
  // Debounce for 1 second
  dailyLimitTimeout = setTimeout(async () => {
    try {
      const limit = parseInt(value) || 0;
      if (limit < 0) {
        showMessage('Daily limit must be 0 or greater', 'danger');
        return;
      }
      
      updatingLimit.value = { ...updatingLimit.value, [barcode.id]: true };
      const res = await apiUpdateBarcodeDailyLimit(barcode.id, limit);
      if (res?.status === 'success' && res?.barcode) {
        // Update local barcode data
        const idx = barcodes.value.findIndex(b => Number(b.id) === Number(barcode.id));
        if (idx !== -1) {
          barcodes.value[idx] = { 
            ...barcodes.value[idx], 
            daily_usage_limit: res.barcode.daily_usage_limit,
            usage_stats: res.barcode.usage_stats 
          };
        }
        showMessage(`Daily limit set to ${limit === 0 ? 'unlimited' : limit}`, 'success');
      }
    } catch (e) {
      showMessage('Failed to update daily limit: ' + (e?.message || 'Unknown error'), 'danger');
    } finally {
      updatingLimit.value = { ...updatingLimit.value, [barcode.id]: false };
    }
  }, 1000);
}

function incrementDailyLimit(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const current = Number(barcode.daily_usage_limit || 0);
  const next = current === 0 ? 1 : current + 1;
  // Optimistic UI update
  barcode.daily_usage_limit = next;
  updateDailyLimit(barcode, next);
}

function decrementDailyLimit(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const current = Number(barcode.daily_usage_limit || 0);
  const next = Math.max(0, current - 1);
  barcode.daily_usage_limit = next;
  updateDailyLimit(barcode, next);
}

function toggleUnlimited(barcode) {
  if (!barcode || !barcode.is_owned_by_current_user) return;
  const next = (Number(barcode.daily_usage_limit || 0) === 0) ? 1 : 0;
  barcode.daily_usage_limit = next;
  updateDailyLimit(barcode, next);
}

// Scroll to add section
function scrollToAdd() {
  if (addSection.value) {
    addSection.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function goToAddTab() {
  activeTab.value = 'Add';
  nextTick(() => {
    if (addSection.value) {
      addSection.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

// Format relative time
function formatRelativeTime(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  
  return date.toLocaleDateString();
}

// setting change handler
function onSettingChange() {
  // debounce logic, 800ms delay to avoid frequent api calls
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }

  saveTimeout = setTimeout(() => {
    autoSaveSettings();
  }, 800);
}

// Set active barcode directly from the list
async function setActiveBarcode(barcode) {
  if (!barcode) return;
  // No-op if already active
  if (Number(settings.value.barcode) === Number(barcode.id)) return;
  settings.value.barcode = Number(barcode.id);
  await autoSaveSettings();
}


// Scanner functions
async function toggleScanner() {
  if (showScanner.value) {
    stopScanner();
    showScanner.value = false;
  } else {
    showScanner.value = true;
    await nextTick();
    const granted = await ensureCameraPermission();
    if (!granted) {
      scanning.value = false;
      scannerStatus.value = 'Camera permission is required to use the scanner.';
      showMessage('Camera permission is required to use the scanner.', 'danger');
      return;
    }
    await startScanner();
  }
}

async function startScanner() {
  try {
    scanning.value = true;
    scannerStatus.value = 'Initializing scanner...';

    const {BrowserMultiFormatReader} = await import('@zxing/library');
    codeReader = new BrowserMultiFormatReader();

    if (!hasCameraPermission.value) {
      const granted = await ensureCameraPermission();
      if (!granted) {
        scannerStatus.value = 'Camera permission denied.';
        scanning.value = false;
        return;
      }
    }

    if (cameras.value.length === 0) {
      const videoInputDevices = await codeReader.listVideoInputDevices();
      cameras.value = videoInputDevices;
      if (videoInputDevices.length > 0) {
        if (!selectedCameraId.value) {
          selectedCameraId.value = videoInputDevices[0].deviceId;
        }
      } else {
        scannerStatus.value = 'No cameras found.';
        scanning.value = false;
        return;
      }
    }

    if (!selectedCameraId.value) {
      scannerStatus.value = 'No camera selected.';
      scanning.value = false;
      return;
    }

    scannerStatus.value = 'Position the barcode within the camera view';

    codeReader.decodeFromVideoDevice(
        selectedCameraId.value,
        videoRef.value,
        (result, error) => {
          if (result) {
            newBarcode.value = result.getText();
            showMessage('Barcode scanned successfully!', 'success');
            stopScanner();
          }

          if (error && error.name !== 'NotFoundException') {
            // This error is expected when no barcode is in view.
          }
        }
    );
  } catch (error) {
    scannerStatus.value = `Failed to start scanner: ${error.message}`;
    scanning.value = false;
  }
}

function stopScanner() {
  if (codeReader) {
    codeReader.reset();
    codeReader = null;
  }
  showScanner.value = false;
  scanning.value = false;
  scannerStatus.value = 'Position the barcode within the camera view';
  cameras.value = [];
}

async function ensureCameraPermission() {
  try {
    if (!navigator?.mediaDevices?.getUserMedia) {
      scannerStatus.value = 'Camera is not supported in this browser.';
      return false;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    // Immediately stop tracks; we only needed to trigger permission
    stream.getTracks().forEach(t => t.stop());
    hasCameraPermission.value = true;
    return true;
  } catch (err) {
    hasCameraPermission.value = false;
    if (err && (err.name === 'NotAllowedError' || err.name === 'SecurityError')) {
      scannerStatus.value = 'Camera permission was denied. Please enable it in browser settings.';
    } else if (err && err.name === 'NotFoundError') {
      scannerStatus.value = 'No camera device found.';
    } else {
      scannerStatus.value = `Unable to access camera: ${err?.message || 'Unknown error'}`;
    }
    return false;
  }
}

// Utility functions
function showMessage(msg, type = 'success') {
  message.value = msg;
  messageType.value = type;

  // Auto-hide after 5 seconds
  setTimeout(() => {
    message.value = '';
  }, 5000);
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Get association status text
function getAssociationStatusText() {
  if (settings.value.associate_user_profile_with_barcode) {
    return 'Active - Profile associated with barcode';
  }
  return 'Inactive - No profile association';
}

// Get barcode display title
function getBarcodeDisplayTitle(barcodeType) {
  switch (barcodeType) {
    case 'DynamicBarcode':
      return 'Dynamic Barcode';
    case 'Others':
      return 'Barcode';
    case 'Identification':
      return 'Identification Barcode';
    default:
      return 'Barcode';
  }
}

// Get barcode display ID
function getBarcodeDisplayId(barcode) {
  switch (barcode.barcode_type) {
    case 'DynamicBarcode':
      return `Dynamic •••• ${barcode.barcode.slice(-4)}`;
    case 'Others':
      return `Barcode ending with ${barcode.barcode.slice(-4)}`;
    case 'Identification':
      return 'Identification Barcode';
    default:
      return `•••• ${barcode.barcode.slice(-4)}`;
  }
}

function getBarcodeTypeLabel(type) {
  if (type === 'DynamicBarcode') return 'Dynamic';
  if (type === 'Identification') return 'Identification';
  return 'Static';
}

function getProfileLabel(barcode) {
  if (!barcode.profile_info) return 'Profile';
  
  const { name, information_id, has_avatar } = barcode.profile_info;
  
  // Show name if available and not too long
  if (name && name.length <= 15) {
    return name;
  }
  
  // Show information ID if available and name is too long or not available
  if (information_id) {
    // Show last 4 digits if it's a long ID number
    if (information_id.length > 8 && /^\d+$/.test(information_id)) {
      return `ID: ${information_id.slice(-4)}`;
    }
    // Show full ID if it's short or contains letters
    return `ID: ${information_id}`;
  }
  
  // Fallback to generic label with avatar indicator
  return has_avatar ? 'Profile+' : 'Profile';
}

function getProfileTooltip(barcode) {
  if (!barcode.profile_info) return 'Profile attached';
  
  const { name, information_id, has_avatar } = barcode.profile_info;
  const parts = [];
  
  if (name) parts.push(`Name: ${name}`);
  if (information_id) parts.push(`ID: ${information_id}`);
  if (has_avatar) parts.push('Has avatar image');
  
  return parts.length ? parts.join('\n') : 'Profile attached';
}

// Get current barcode info
const currentBarcodeInfo = computed(() => {
  if (!settings.value.barcode) return null;
  const current = barcodeChoices.value.find(c => Number(c.id) === Number(settings.value.barcode));
  if (!current) return null;
  
  // Check if it's an Identification barcode
  if (current.barcode_type === 'Identification') {
    return `${current.barcode_type}`;
  }
  
  // For other barcode types, show last 4 digits
  return `${current.barcode_type} ending with ...${current.barcode.slice(-4)}`;
});


// Lifecycle
onMounted(() => {
  loadDashboard();
});

onUnmounted(() => {
  stopScanner();
  // Clear save timeout
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  // Clear daily limit timeout
  if (dailyLimitTimeout) {
    clearTimeout(dailyLimitTimeout);
  }
});


watch(selectedCameraId, async (newId, oldId) => {
  if (showScanner.value && newId && oldId && newId !== oldId) {
    if (codeReader) {
      codeReader.reset();
    }
    await nextTick();
    await startScanner();
  }
});

watch(showScanner, (newValue) => {
  if (!newValue) {
    stopScanner();
  }
});
</script>

<!-- Styles moved to external CSS: see @/assets/css/BarcodeDashboard.css -->