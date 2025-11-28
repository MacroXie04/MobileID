<template>
  <section class="dashboard-card md-mb-6">
    <div class="card-header">
      <div class="header-icon-wrapper">
      <md-icon>inventory_2</md-icon>
      </div>
      <h2 class="md-typescale-headline-small">Available Barcodes</h2>
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
        class="barcode-card"
      >
        <!-- Card Header: Icon + Title + Status -->
        <div class="barcode-card-header">
          <div class="barcode-type-icon">
            <md-icon aria-hidden="true">{{ iconForType(barcode.barcode_type) }}</md-icon>
          </div>
          <div class="barcode-header-content">
            <div class="barcode-title-row">
              <h3 class="barcode-title">{{ getBarcodeDisplayTitle(barcode.barcode_type) }}</h3>
              <span class="barcode-type-label">{{ getBarcodeTypeLabel(barcode.barcode_type) }}</span>
            </div>
            <p class="barcode-id">{{ getBarcodeDisplayId(barcode) }}</p>
          </div>
          <!-- Active Badge -->
          <div v-if="Number(settings.barcode) === Number(barcode.id)" class="active-badge">
            <md-icon>check_circle</md-icon>
            <span>Active</span>
          </div>
        </div>

        <!-- Owner & Share Info -->
        <div v-if="barcode.owner || !barcode.is_owned_by_current_user || (barcode.barcode_type === 'DynamicBarcode' && barcode.has_profile_addon)" class="barcode-meta">
          <md-assist-chip v-if="barcode.owner" has-icon>
            <md-icon slot="icon">person</md-icon>
            {{ barcode.owner }}
          </md-assist-chip>
          <md-assist-chip v-if="!barcode.is_owned_by_current_user" has-icon>
            <md-icon slot="icon">group</md-icon>
            Shared with you
          </md-assist-chip>
          <md-assist-chip
            v-if="barcode.barcode_type === 'DynamicBarcode' && barcode.has_profile_addon"
            :title="getProfileTooltip(barcode)"
            has-icon
          >
            <md-icon slot="icon">{{ barcode.profile_info?.has_avatar ? 'account_circle' : 'badge' }}</md-icon>
            {{ getProfileLabel(barcode) }}
          </md-assist-chip>
        </div>

        <!-- Usage Stats -->
        <div
          v-if="barcode.barcode_type !== 'Identification'"
          class="barcode-stats-row"
        >
          <div class="stat-item">
            <md-icon>trending_up</md-icon>
            <span class="stat-value">{{ barcode.usage_count || 0 }}</span>
            <span class="stat-label">scans</span>
          </div>
          <div v-if="barcode.last_used" class="stat-item">
            <md-icon>schedule</md-icon>
            <span class="stat-value">{{ formatRelativeTime(barcode.last_used) }}</span>
          </div>
          <div v-if="barcode.usage_stats" class="stat-item">
            <md-icon>today</md-icon>
            <span class="stat-value">{{ barcode.usage_stats.daily_used }}</span>
            <span class="stat-label">today</span>
          </div>
        </div>

        <!-- Daily Limit Section -->
        <div
          v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
          class="barcode-limit-section"
        >
          <div class="limit-row">
            <div class="limit-label">
              <md-icon>event</md-icon>
              <span>Daily Limit</span>
            </div>
            <div class="limit-toggle">
              <span class="toggle-label">{{ Number(barcode.daily_usage_limit || 0) === 0 ? 'Unlimited' : barcode.daily_usage_limit + '/day' }}</span>
              <md-switch
                :selected="Number(barcode.daily_usage_limit || 0) === 0"
                @change="(e) => $emit('toggle-unlimited-switch', barcode, e)"
              ></md-switch>
            </div>
          </div>
          <transition name="expand">
            <div v-if="Number(barcode.daily_usage_limit || 0) !== 0" class="limit-controls-row">
              <md-icon-button @click="$emit('decrement-limit', barcode)">
                <md-icon>remove</md-icon>
              </md-icon-button>
              <md-outlined-text-field
                :value="barcode.daily_usage_limit || 0"
                class="limit-input"
                min="1"
                type="number"
                @input="(e) => $emit('update-limit', barcode, e.target.value)"
              ></md-outlined-text-field>
              <md-icon-button @click="$emit('increment-limit', barcode)">
                <md-icon>add</md-icon>
              </md-icon-button>
              <div class="limit-presets">
                <md-assist-chip @click="$emit('apply-limit-preset', barcode, 10)">10</md-assist-chip>
                <md-assist-chip @click="$emit('apply-limit-preset', barcode, 15)">15</md-assist-chip>
                <md-assist-chip @click="$emit('apply-limit-preset', barcode, 20)">20</md-assist-chip>
              </div>
              <md-circular-progress v-if="updatingLimit[barcode.id]" indeterminate></md-circular-progress>
            </div>
          </transition>
        </div>

        <!-- Card Actions -->
        <div class="barcode-card-actions">
          <md-filled-tonal-button
            v-if="Number(settings.barcode) !== Number(barcode.id)"
            :disabled="pullSettings.pull_setting === 'Enable'"
            :title="pullSettings.pull_setting === 'Enable' ? 'Disabled when auto-pull is enabled' : 'Set as active barcode'"
            @click="$emit('set-active', barcode)"
          >
            <md-icon slot="icon">check_circle</md-icon>
            Set Active
          </md-filled-tonal-button>
          <md-outlined-button
            v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
            @click="$emit('toggle-share', barcode)"
          >
            <md-icon slot="icon">{{ barcode.share_with_others ? 'lock_open' : 'lock' }}</md-icon>
            {{ barcode.share_with_others ? 'Public' : 'Private' }}
          </md-outlined-button>
          <md-icon-button
            v-if="barcode.is_owned_by_current_user && barcode.barcode_type !== 'Identification'"
            @click="$emit('delete', barcode)"
          >
            <md-icon>delete</md-icon>
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
import {
  emitsDefinition,
  propsDefinition,
  useBarcodesListCardSetup,
} from './BarcodesListCard.setup.js';

defineProps(propsDefinition);
defineEmits(emitsDefinition);

const {
  iconForType,
  getBarcodeDisplayTitle,
  getBarcodeTypeLabel,
  getProfileLabel,
  getProfileTooltip,
  getBarcodeDisplayId,
  formatRelativeTime,
} = useBarcodesListCardSetup();
</script>
