<template>
  <section class="dashboard-card md-mb-6">
    <div class="card-header">
      <div class="header-icon-wrapper">
        <md-icon>inventory_2</md-icon>
      </div>
      <h2 class="md-typescale-headline-small">Available Barcodes</h2>
    </div>
    <!-- Filter Bar -->
    <BarcodeFilterBar
      :filter-type="filterType"
      :owned-only="ownedOnly"
      @update-filter="(value) => $emit('update-filter', value)"
      @toggle-owned="$emit('toggle-owned')"
    />
    <transition-group
      v-if="filteredBarcodes.length > 0"
      class="barcodes-grid md-grid-container md-gap-4"
      name="list"
      tag="div"
    >
      <BarcodeListItem
        v-for="barcode in filteredBarcodes"
        :key="barcode.barcode_uuid"
        :barcode="barcode"
        :is-active="settings.barcode === barcode.barcode_uuid"
        :pull-enabled="pullSettings.pull_setting === 'Enable'"
        :updating="updatingLimit[barcode.barcode_uuid]"
        @set-active="(b) => $emit('set-active', b)"
        @toggle-share="(b) => $emit('toggle-share', b)"
        @delete="(b) => $emit('delete', b)"
        @update-limit="(b, value) => $emit('update-limit', b, value)"
        @increment-limit="(b) => $emit('increment-limit', b)"
        @decrement-limit="(b) => $emit('decrement-limit', b)"
        @toggle-unlimited-switch="(b, e) => $emit('toggle-unlimited-switch', b, e)"
        @apply-limit-preset="(b, value) => $emit('apply-limit-preset', b, value)"
      />
    </transition-group>
    <BarcodesEmptyState v-else :has-active-filters="hasActiveFilters" />
  </section>
</template>

<script setup lang="ts">
import { emitsDefinition, propsDefinition } from './BarcodesListCard.setup';
import BarcodeFilterBar from './list/BarcodeFilterBar.vue';
import BarcodeListItem from './list/BarcodeListItem.vue';
import BarcodesEmptyState from './list/BarcodesEmptyState.vue';

defineProps(propsDefinition);
defineEmits(emitsDefinition);
</script>
