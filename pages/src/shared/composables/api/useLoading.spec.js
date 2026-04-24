import { beforeEach, describe, expect, it } from 'vitest';
import { useLoading } from '@shared/composables/api/useLoading';

describe('useLoading', () => {
  let loading;

  beforeEach(() => {
    // Force reset singleton state
    loading = useLoading();
    loading.forceStopLoading();
  });

  describe('startLoading', () => {
    it('should set isLoading to true', () => {
      loading.startLoading();
      expect(loading.isLoading.value).toBe(true);
    });

    it('should set default loading message', () => {
      loading.startLoading();
      expect(loading.loadingMessage.value).toBe('Loading...');
    });

    it('should set custom loading message', () => {
      loading.startLoading('Saving data...');
      expect(loading.loadingMessage.value).toBe('Saving data...');
    });
  });

  describe('stopLoading', () => {
    it('should stop loading when all requests complete', () => {
      loading.startLoading();
      loading.stopLoading();
      expect(loading.isLoading.value).toBe(false);
    });

    it('should remain loading when multiple requests are active', () => {
      loading.startLoading('First');
      loading.startLoading('Second');
      loading.stopLoading(); // first completes
      expect(loading.isLoading.value).toBe(true);
    });

    it('should stop loading when all concurrent requests complete', () => {
      loading.startLoading();
      loading.startLoading();
      loading.stopLoading();
      loading.stopLoading();
      expect(loading.isLoading.value).toBe(false);
      expect(loading.loadingMessage.value).toBe('');
    });

    it('should not go below zero active requests', () => {
      loading.stopLoading();
      loading.stopLoading();
      expect(loading.isLoading.value).toBe(false);
    });
  });

  describe('forceStopLoading', () => {
    it('should immediately stop all loading', () => {
      loading.startLoading();
      loading.startLoading();
      loading.startLoading();
      loading.forceStopLoading();
      expect(loading.isLoading.value).toBe(false);
      expect(loading.loadingMessage.value).toBe('');
    });
  });

  describe('setLoadingMessage', () => {
    it('should update message without changing loading state', () => {
      loading.setLoadingMessage('Processing...');
      expect(loading.loadingMessage.value).toBe('Processing...');
      expect(loading.isLoading.value).toBe(false);
    });

    it('should update message while loading', () => {
      loading.startLoading('Initial');
      loading.setLoadingMessage('Updated');
      expect(loading.loadingMessage.value).toBe('Updated');
      expect(loading.isLoading.value).toBe(true);
    });
  });

  describe('singleton behavior', () => {
    it('should share state across instances', () => {
      const instance1 = useLoading();
      const instance2 = useLoading();

      instance1.startLoading('From instance 1');
      expect(instance2.isLoading.value).toBe(true);
      expect(instance2.loadingMessage.value).toBe('From instance 1');
    });
  });
});
