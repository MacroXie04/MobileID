<template>
  <section class="md-card md-mb-6">
    <div class="card-header md-flex md-items-center md-gap-3 md-mb-4">
      <md-icon>inventory_2</md-icon>
      <h2 class="md-typescale-headline-small md-m-0">Available Barcodes</h2>
    </div>
    <!-- Filter Bar -->
    <div class="filter-bar md-flex md-gap-3 md-items-center md-mb-6 md-flex-wrap">
      <div class="filter-controls md-flex md-items-center md-gap-2">
        <md-filter-chip :selected="filterType === 'All'" @click="$emit('update-filter', 'All')"
          >All</md-filter-chip
        >
        <md-filter-chip
          :selected="filterType === 'Dynamic'"
          @click="$emit('update-filter', 'Dynamic')"
          >Dynamic
        </md-filter-chip>
        <md-filter-chip
          :selected="filterType === 'Static'"
          @click="$emit('update-filter', 'Static')"
          >Static
        </md-filter-chip>
        <md-filter-chip
          :selected="filterType === 'Identification'"
          @click="$emit('update-filter', 'Identification')"
        >
          Identification
        </md-filter-chip>
        <md-divider vertical></md-divider>
        <md-filter-chip :selected="ownedOnly" @click="$emit('toggle-owned')">
          <md-icon slot="icon">person</md-icon>
          Owned only
        </md-filter-chip>
      </div>
    </div>
    <transition-group
      v-if="filteredBarcodes.length > 0"
      class="barcodes-grid md-grid-container md-gap-4"
      name="list"
      tag="div"
    >
      <article
        v-for="barcode in filteredBarcodes"
        :key="barcode.id"
        :class="{
          'is-active': Number(settings.barcode) === Number(barcode.id),
          'is-shared': !barcode.is_owned_by_current_user,
        }"
        class="barcode-item md-card md-p-5 md-flex md-items-center md-gap-4"
      >
        <div class="barcode-type-icon md-flex md-items-center md-justify-center md-rounded-lg">
          <md-icon aria-hidden="true">{{ iconForType(barcode.barcode_type) }}</md-icon>
        </div>
        <div class="barcode-content">
          <div class="barcode-title-row">
            <h3 class="md-typescale-title-medium md-m-0">
              {{ getBarcodeDisplayTitle(barcode.barcode_type) }}
            </h3>
            <div class="barcode-badges md-flex md-gap-2 md-flex-wrap">
              <md-assist-chip has-icon>
                <template #icon>
                  <md-icon aria-hidden="true">{{ iconForType(barcode.barcode_type) }}</md-icon>
                </template>
                {{ getBarcodeTypeLabel(barcode.barcode_type) }}
              </md-assist-chip>
              <md-assist-chip
                v-if="Number(settings.barcode) === Number(barcode.id)"
                aria-label="Active barcode"
                data-aria-label="Active barcode"
                has-icon
              >
                <template #icon>
                  <md-icon aria-hidden="true">check_circle</md-icon>
                </template>
                Active
              </md-assist-chip>
              <md-assist-chip
                v-if="barcode.owner"
                aria-label="Owner"
                data-aria-label="Owner"
                has-icon
              >
                <template #icon>
                  <md-icon aria-hidden="true">person</md-icon>
                </template>
                {{ barcode.owner }}
              </md-assist-chip>
              <md-assist-chip
                v-if="!barcode.is_owned_by_current_user"
                aria-label="Shared barcode"
                data-aria-label="Shared barcode"
              >
                <template #icon>
                  <md-icon aria-hidden="true">group</md-icon>
                </template>
                Shared
              </md-assist-chip>
              <md-assist-chip
                v-if="barcode.barcode_type === 'DynamicBarcode' && barcode.has_profile_addon"
                :title="getProfileTooltip(barcode)"
                has-icon
              >
                <template #icon>
                  <md-icon aria-hidden="true"
                    >{{ barcode.profile_info?.has_avatar ? 'account_circle' : 'badge' }}
                  </md-icon>
                </template>
                {{ getProfileLabel(barcode) }}
              </md-assist-chip>
            </div>
          </div>
          <p class="barcode-id md-typescale-body-medium md-mt-2 md-mb-0">
            {{ getBarcodeDisplayId(barcode) }}
            <span v-if="!barcode.is_owned_by_current_user && barcode.owner" class="owner-label"
              >by {{ barcode.owner }}</span
            >
          </p>
          <div
            v-if="barcode.barcode_type !== 'Identification' && barcode.usage_count > 0"
            class="barcode-stats md-flex md-gap-4 md-flex-wrap md-mt-3"
          >
            <span class="stat md-flex md-items-center md-gap-1"
              ><md-icon aria-hidden="true">trending_up</md-icon>{{ barcode.usage_count }} scan{{
                barcode.usage_count !== 1 ? 's' : ''
              }}</span
            >
            <span v-if="barcode.last_used" class="stat md-flex md-items-center md-gap-1"
              ><md-icon aria-hidden="true">schedule</md-icon
              >{{ formatRelativeTime(barcode.last_used) }}</span
            >
            <span v-if="barcode.usage_stats" class="stat md-flex md-items-center md-gap-1"
              ><md-icon aria-hidden="true">today</md-icon
              >{{ barcode.usage_stats.daily_used }} today<span
                v-if="barcode.usage_stats.daily_limit > 0"
                >/ {{ barcode.usage_stats.daily_limit }}</span
              ></span
            >
          </div>
          <div
            v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
            class="barcode-limit-controls md-mt-3"
          >
            <div class="limit-header md-flex md-items-center md-gap-3">
              <div class="limit-header-left md-flex md-items-center md-gap-2">
                <md-icon aria-hidden="true" class="limit-icon">event</md-icon>
                <div>
                  <div class="md-typescale-label-large">Daily Limit</div>
                </div>
              </div>
              <div class="md-ml-auto md-flex md-items-center md-gap-2">
                <span class="md-typescale-label-small">Unlimited</span>
                <md-switch
                  :selected="Number(barcode.daily_usage_limit || 0) === 0"
                  @change="(e) => $emit('toggle-unlimited-switch', barcode, e)"
                ></md-switch>
              </div>
            </div>
            <div class="limit-controls md-flex md-items-center md-gap-2 md-mt-3">
              <md-icon-button
                :disabled="Number(barcode.daily_usage_limit || 0) === 0"
                aria-label="Decrease daily limit"
                data-aria-label="Decrease daily limit"
                @click="$emit('decrement-limit', barcode)"
              >
                <md-icon aria-hidden="true">remove</md-icon>
              </md-icon-button>
              <md-outlined-text-field
                :disabled="Number(barcode.daily_usage_limit || 0) === 0"
                :value="barcode.daily_usage_limit || 0"
                class="limit-input"
                label="Daily Limit"
                min="0"
                type="number"
                @input="(e) => $emit('update-limit', barcode, e.target.value)"
              >
                <md-icon slot="leading-icon">pin</md-icon>
              </md-outlined-text-field>
              <md-icon-button
                :disabled="Number(barcode.daily_usage_limit || 0) === 0"
                aria-label="Increase daily limit"
                data-aria-label="Increase daily limit"
                @click="$emit('increment-limit', barcode)"
              >
                <md-icon aria-hidden="true">add</md-icon>
              </md-icon-button>
              <div class="limit-presets md-flex md-items-center md-gap-1 md-ml-2">
                <md-assist-chip @click="$emit('apply-limit-preset', barcode, 10)"
                  >10</md-assist-chip
                >
                <md-assist-chip @click="$emit('apply-limit-preset', barcode, 15)"
                  >15</md-assist-chip
                >
              </div>
              <md-circular-progress
                v-if="updatingLimit[barcode.id]"
                indeterminate
              ></md-circular-progress>
            </div>
          </div>
        </div>
        <div class="barcode-actions md-flex md-items-center md-gap-2">
          <md-filled-tonal-button
            v-if="Number(settings.barcode) !== Number(barcode.id)"
            :disabled="pullSettings.pull_setting === 'Enable'"
            :title="
              pullSettings.pull_setting === 'Enable'
                ? 'Barcode selection is disabled when pull setting is enabled'
                : 'Set this barcode as active'
            "
            @click="$emit('set-active', barcode)"
          >
            <md-icon slot="icon">check_circle</md-icon>
            Set Active
          </md-filled-tonal-button>
          <md-assist-chip
            v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
            :selected="!!barcode.share_with_others"
            aria-label="Share with others"
            data-aria-label="Share with others"
            has-icon
            @click="$emit('toggle-share', barcode)"
          >
            <template #icon>
              <md-icon aria-hidden="true">{{
                barcode.share_with_others ? 'share' : 'lock'
              }}</md-icon>
            </template>
            {{ barcode.share_with_others ? 'Shared' : 'Private' }}
          </md-assist-chip>
          <md-icon-button
            v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
            @click="$emit('delete', barcode)"
          >
            <md-icon aria-hidden="true">delete</md-icon>
          </md-icon-button>
        </div>
      </article>
    </transition-group>
    <div v-else class="md-empty-state empty-state-box">
      <md-icon class="md-empty-state-icon">qr_code_scanner</md-icon>
      <h3 class="md-typescale-headline-small md-mb-2">
        {{ hasActiveFilters ? 'No barcodes match your filters' : 'No barcodes found' }}
      </h3>
      <p class="md-typescale-body-medium md-m-0">
        {{
          hasActiveFilters
            ? 'Try clearing filters or selecting a different type.'
            : 'Add your first barcode to get started.'
        }}
      </p>
    </div>
  </section>
</template>

<script setup>
defineEmits([
  'update-filter',
  'toggle-owned',
  'set-active',
  'toggle-share',
  'delete',
  'update-limit',
  'increment-limit',
  'decrement-limit',
  'toggle-unlimited-switch',
  'apply-limit-preset',
]);

defineProps({
  activeTab: { type: String, default: 'Barcodes' },
  settings: { type: Object, required: true },
  pullSettings: {
    type: Object,
    default: () => ({ pull_setting: 'Disable', gender_setting: 'Unknow' }),
  },
  filteredBarcodes: { type: Array, default: () => [] },
  hasActiveFilters: { type: Boolean, default: false },
  filterType: { type: String, default: 'All' },
  ownedOnly: { type: Boolean, default: false },
  updatingLimit: { type: Object, default: () => ({}) },
});

function iconForType(type) {
  if (type === 'DynamicBarcode') return 'qr_code_2';
  if (type === 'Identification') return 'badge';
  return 'barcode';
}

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

function getBarcodeTypeLabel(type) {
  if (type === 'DynamicBarcode') return 'Dynamic';
  if (type === 'Identification') return 'Identification';
  return 'Static';
}

function getProfileLabel(barcode) {
  if (!barcode.profile_info) return 'Profile';
  const { name, information_id, has_avatar } = barcode.profile_info;
  if (name && name.length <= 15) return name;
  if (information_id) {
    if (information_id.length > 8 && /^\d+$/.test(information_id))
      return `ID: ${information_id.slice(-4)}`;
    return `ID: ${information_id}`;
  }
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
</script>
