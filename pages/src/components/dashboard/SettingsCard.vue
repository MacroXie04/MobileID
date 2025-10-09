<template>
  <section class="settings-card md-card md-mb-6">
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
      <transition name="scale-fade">

        <!--current settings barcode display-->
        <div v-if="currentBarcodeInfo" class="settings-section md-mb-6">
          <div class="active-barcode-header">
            <md-icon class="active-icon pulse">verified</md-icon>
            <span class="md-typescale-label-medium">CURRENTLY ACTIVE</span>
          </div>
          <div class="active-barcode-info">
            <div class="barcode-type-badge">
              <md-icon>
                {{ activeIcon }}
              </md-icon>
            </div>
            <div class="barcode-details">
              <h3 class="md-typescale-title-medium md-m-0">{{ currentBarcodeInfo }}</h3>
              <p v-if="selectedBarcode && selectedBarcode.barcode_type !== 'Identification'"
                 class="md-typescale-body-small md-m-0 md-mt-1">
                {{ selectedBarcode.usage_count || 0 }} total scans
                <span v-if="selectedBarcode.last_used">• Last used {{
                    formatRelativeTime(selectedBarcode.last_used)
                  }}</span>
              </p>
            </div>
          </div>
        </div>
      </transition>

      <!--barcode usage statistics-->
      <div
          v-if="selectedBarcode && selectedBarcode.barcode_type !== 'Identification' && selectedBarcode.usage_count > 0"
          class="settings-section md-mb-6">
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
          <div v-if="selectedBarcode.recent_transactions && selectedBarcode.recent_transactions.length > 0"
               class="activity-list">
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

      <!--dynamic barcode settings-->
      <div
        v-if="isDynamicSelected && currentBarcodeHasProfile"
        class="settings-section md-mb-6"
      >
        <div class="active-barcode-header">
          <md-icon class="active-icon pulse">qr_code_2</md-icon>
          <span class="md-typescale-label-medium">Dynamic Barcode Settings</span>
        </div>
        <md-list>
          <md-list-item>
            <md-icon slot="start">person_pin</md-icon>
            <div slot="headline">Profile Association</div>
            <div slot="supporting-text">Use profile data from the ID server</div>
            <md-switch
              slot="end"
              :selected="associateUserProfileWithBarcode"
              :disabled="isUserGroup"
              @change="(e) => $emit('update-associate', e.target.selected)"
            ></md-switch>
          </md-list-item>

          <md-divider inset></md-divider>

          <md-list-item>
            <md-icon slot="start">security</md-icon>
            <div slot="headline">Server Verification</div>
            <div slot="supporting-text">Validate on server (may take longer or fail)</div>
            <md-switch
              slot="end"
              :selected="serverVerification"
              @change="(e) => $emit('update-server', e.target.selected)"
            ></md-switch>
          </md-list-item>
        </md-list>
      </div>

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

      <div v-if="hasErrors" class="md-banner md-banner-error md-mt-4">
        <md-icon>error</md-icon>
        <div class="error-messages">
          <p v-for="(error, field) in errors" :key="field" class="md-typescale-body-medium md-m-0">
            {{ error }}
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import {computed} from 'vue';

const props = defineProps({
  isSaving: {type: Boolean, default: false},
  currentBarcodeInfo: {type: String, default: ''},
  selectedBarcode: {type: Object, default: null},
  barcodeChoices: {type: Array, default: () => []},
  settings: {type: Object, default: () => ({})},
  isUserGroup: {type: Boolean, default: false},
  isDynamicSelected: {type: Boolean, default: false},
  currentBarcodeHasProfile: {type: Boolean, default: false},
  errors: {type: Object, default: () => ({})},
  associateUserProfileWithBarcode: {type: Boolean, default: false},
  serverVerification: {type: Boolean, default: false},
  formatRelativeTime: {type: Function, required: true},
  formatDate: {type: Function, required: true}
});

defineEmits(['update-associate', 'update-server']);

const hasErrors = computed(() => Object.keys(props.errors || {}).length > 0);

const activeIcon = computed(() => {
  const id = props.settings?.barcode ? Number(props.settings.barcode) : null;
  const current = (props.barcodeChoices || []).find(c => Number(c.id) === id);
  if (!current) return 'barcode';
  if (current.barcode_type === 'DynamicBarcode') return 'qr_code_2';
  if (current.barcode_type === 'Identification') return 'badge';
  return 'barcode';
});
</script>

<style scoped>
.settings-section {
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--md-sys-color-outline-variant);
}
</style>
