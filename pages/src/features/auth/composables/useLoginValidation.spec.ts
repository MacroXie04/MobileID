import { beforeEach, describe, expect, it } from 'vitest';

import { useLoginValidation } from '@auth/composables/useLoginValidation';

describe('useLoginValidation', () => {
  let validation;

  beforeEach(() => {
    validation = useLoginValidation();
  });

  it('accepts valid username and password', () => {
    const isValid = validation.validateForm({
      username: 'alice',
      password: 'pw',
    });

    expect(isValid).toBe(true);
    expect(validation.errors.username).toBeUndefined();
    expect(validation.errors.password).toBeUndefined();
  });

  it('rejects an empty username', () => {
    const isValid = validation.validateForm({ username: '', password: 'pw' });

    expect(isValid).toBe(false);
    expect(validation.errors.username).toBe('Username is required');
  });

  it('treats whitespace-only usernames as missing', () => {
    const isValid = validation.validateForm({
      username: '   ',
      password: 'pw',
    });

    expect(isValid).toBe(false);
    expect(validation.errors.username).toBe('Username is required');
  });

  it('rejects usernames shorter than 3 characters', () => {
    const isValid = validation.validateForm({
      username: 'ab',
      password: 'pw',
    });

    expect(isValid).toBe(false);
    expect(validation.errors.username).toBe('Username must be at least 3 characters');
  });

  it('rejects an empty password', () => {
    const isValid = validation.validateForm({
      username: 'alice',
      password: '',
    });

    expect(isValid).toBe(false);
    expect(validation.errors.password).toBe('Password is required');
  });

  it('flags both username and password errors in a single pass', () => {
    const isValid = validation.validateForm({ username: '', password: '' });

    expect(isValid).toBe(false);
    expect(validation.errors.username).toBe('Username is required');
    expect(validation.errors.password).toBe('Password is required');
  });

  it('validateField only touches the targeted field', () => {
    validation.validateField('username', { username: '', password: '' });

    expect(validation.errors.username).toBe('Username is required');
    expect(validation.errors.password).toBeUndefined();
  });

  it('clearError removes a specific field error', () => {
    validation.validateForm({ username: '', password: '' });
    validation.clearError('username');

    expect(validation.errors.username).toBeUndefined();
    expect(validation.errors.password).toBe('Password is required');
  });

  it('clearing username or password also clears general error', () => {
    validation.setGeneralError('Incorrect credentials');
    validation.clearError('username');

    expect(validation.errors.general).toBeUndefined();
  });

  it('clearing an unrelated field does not clear the general error', () => {
    validation.setGeneralError('Network down');
    validation.clearError('captcha');

    expect(validation.errors.general).toBe('Network down');
  });

  it('setGeneralError records a message under errors.general', () => {
    validation.setGeneralError('Account locked');

    expect(validation.errors.general).toBe('Account locked');
  });

  it('validateForm clears stale errors from a previous submit', () => {
    validation.validateForm({ username: '', password: '' });
    expect(validation.errors.username).toBeDefined();

    const isValid = validation.validateForm({
      username: 'alice',
      password: 'pw',
    });

    expect(isValid).toBe(true);
    expect(validation.errors.username).toBeUndefined();
    expect(validation.errors.password).toBeUndefined();
  });

  it('validateForm clears the general error before re-running', () => {
    validation.setGeneralError('Stale error');

    const isValid = validation.validateForm({
      username: 'alice',
      password: 'pw',
    });

    expect(isValid).toBe(true);
    expect(validation.errors.general).toBeUndefined();
  });
});
