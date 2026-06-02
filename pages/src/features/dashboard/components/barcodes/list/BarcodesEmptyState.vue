<template>
  <div class="md-empty-state empty-state-box">
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
</template>

<script setup lang="ts">
// Presentational empty state for the barcodes list.
defineProps({
  hasActiveFilters: { type: Boolean, default: false },
});
</script>

<style scoped>
.empty-state-box {
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-sys-shape-corner-medium);
  padding: var(--md-sys-spacing-4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: var(--md-sys-spacing-2);
  min-height: 160px;
}

.empty-state-box .md-empty-state-icon {
  font-size: 40px;
  color: var(--md-sys-color-on-surface-variant);
}
</style>
