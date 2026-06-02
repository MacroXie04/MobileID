<template>
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
      <md-filter-chip :selected="filterType === 'Static'" @click="$emit('update-filter', 'Static')"
        >Static
      </md-filter-chip>
      <md-divider vertical></md-divider>
      <md-filter-chip :selected="ownedOnly" @click="$emit('toggle-owned')">
        <md-icon slot="icon">person</md-icon>
        Owned only
      </md-filter-chip>
    </div>
  </div>
</template>

<script setup lang="ts">
// Presentational filter chips for the barcodes list. State lives in the parent.
defineProps({
  filterType: { type: String, default: 'All' },
  ownedOnly: { type: Boolean, default: false },
});

defineEmits<{
  'update-filter': [value: string];
  'toggle-owned': [];
}>();
</script>

<style scoped>
/* Keep all chips on a single row with horizontal scroll only */
.filter-controls {
  flex-wrap: nowrap;
  overflow-x: auto;
  overflow-y: hidden;
  width: 100%;
  gap: var(--md-sys-spacing-2);
  padding-bottom: var(--md-sys-spacing-1);
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE 10+ */
  overscroll-behavior-y: none; /* Prevent vertical overscroll */
}

/* WebKit-based browsers */
.filter-controls::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

@media (max-width: 904px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-controls {
    overflow-x: auto;
    padding-bottom: var(--md-sys-spacing-1);
  }
}
</style>
