import { register, userInfo } from '@shared/api/auth.js';
import { ApiError } from '@shared/api/client';

export function useRegisterSubmit({
  formData,
  errors,
  loading,
  router,
  validateForm,
  setServerErrors,
  setGeneralError,
}) {
  const handleSubmit = async () => {
    if (loading.value) return;

    if (!validateForm(formData.value)) {
      return;
    }

    loading.value = true;
    Object.keys(errors).forEach((key) => delete errors[key]);

    try {
      const response = await register(formData.value);

      if (!response.success) {
        if (response.errors) {
          setServerErrors(response.errors);
        } else {
          setGeneralError(
            response.detail ||
              response.message ||
              'Registration failed. Please check your information.'
          );
        }
        return;
      }

      try {
        const user = await userInfo();
        if (user) {
          window.userInfo = user;
          await router.push('/');
        } else {
          await router.push('/login');
        }
      } catch {
        await router.push('/login');
      }
    } catch (error) {
      console.error('Registration error:', error);

      if (error instanceof ApiError) {
        const apiData = error.data || {};
        const apiErrors = apiData.errors || apiData;

        const generalMessages = [];
        if (apiData.detail) generalMessages.push(apiData.detail);
        if (apiData.message) generalMessages.push(apiData.message);
        if (apiErrors.non_field_errors) {
          generalMessages.push(
            Array.isArray(apiErrors.non_field_errors)
              ? apiErrors.non_field_errors.join(' ')
              : apiErrors.non_field_errors
          );
        }

        const fieldErrors =
          apiErrors && typeof apiErrors === 'object' ? { ...apiErrors } : undefined;
        if (fieldErrors) {
          delete fieldErrors.non_field_errors;
          delete fieldErrors.detail;
          delete fieldErrors.message;
          if (Object.keys(fieldErrors).length > 0) {
            setServerErrors(fieldErrors);
          }
        }

        if (generalMessages.length) {
          setGeneralError(generalMessages.join(' '));
        } else if (!fieldErrors || Object.keys(fieldErrors).length === 0) {
          setGeneralError('Registration failed. Please try again.');
        }
        return;
      }

      try {
        const errorData = JSON.parse(error.message);
        if (errorData.message) {
          setGeneralError(errorData.message);
        } else if (errorData.errors) {
          setServerErrors(errorData.errors);
        } else if (errorData && typeof errorData === 'object') {
          setServerErrors(errorData);
        } else {
          setGeneralError('Registration failed. Please try again.');
        }
      } catch (_parseError) {
        setGeneralError(
          error?.message || 'Network error. Please check your connection and try again.'
        );
      }
    } finally {
      loading.value = false;
    }
  };

  return { handleSubmit };
}
