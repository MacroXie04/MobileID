import { beforeEach, describe, expect, it } from 'vitest';

import { useRegisterValidation } from '@auth/composables/register/useRegisterValidation';

describe('useRegisterValidation', () => {
  let validation;

  beforeEach(() => {
    validation = useRegisterValidation();
  });

  it('rejects a single-character password during registration', () => {
    const formData = {
      username: 'testuser',
      name: 'Test User',
      password1: '1',
      password2: '1',
    };

    const isValid = validation.validateForm(formData);

    expect(isValid).toBe(false);
    expect(validation.errors.password1).toBe('Password must be at least 10 characters');
    expect(validation.errors.password2).toBeUndefined();
  });

  it('requires a password', () => {
    const formData = {
      username: 'testuser',
      name: 'Test User',
      password1: '',
      password2: '',
    };

    const isValid = validation.validateForm(formData);

    expect(isValid).toBe(false);
    expect(validation.errors.password1).toBe('Password is required');
    expect(validation.errors.password2).toBe('Please confirm your password');
  });

  it('requires matching passwords', () => {
    const formData = {
      username: 'testuser',
      name: 'Test User',
      password1: '1',
      password2: '2',
    };

    const isValid = validation.validateForm(formData);

    expect(isValid).toBe(false);
    expect(validation.errors.password2).toBe('Passwords do not match');
  });
});
