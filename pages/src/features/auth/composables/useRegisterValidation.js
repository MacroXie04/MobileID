import { reactive } from 'vue';

/**
 * Composable for handling registration form validation
 * @returns {Object} Validation functions and error state
 */
export function useRegisterValidation() {
  const errors = reactive({});

  /**
   * Clears error for a specific field
   * @param {string} field - The field name to clear errors for
   */
  function clearError(field) {
    delete errors[field];
    if (field !== 'general') {
      delete errors.general;
    }
  }

  /**
   * Validates a specific field
   * @param {string} field - The field name to validate
   * @param {Object} formData - The form data object
   */
  function validateField(field, formData) {
    clearError(field);

    switch (field) {
      case 'username':
        if (!formData.username.trim()) {
          errors.username = 'Username is required';
        } else if (formData.username.length < 3) {
          errors.username = 'Username must be at least 3 characters';
        }
        break;

      case 'name':
        if (!formData.name.trim()) {
          errors.name = 'Name is required';
        }
        break;

      case 'information_id':
        if (!formData.information_id.trim()) {
          errors.information_id = 'Information ID is required';
        }
        break;

      case 'password1':
        if (!formData.password1) {
          errors.password1 = 'Password is required';
        }
        break;

      case 'password2':
        if (!formData.password2) {
          errors.password2 = 'Please confirm your password';
        } else if (formData.password1 && formData.password2 !== formData.password1) {
          errors.password2 = 'Passwords do not match';
        }
        break;
    }
  }

  /**
   * Validates the entire registration form
   * @param {Object} formData - The form data object containing all registration fields
   * @returns {boolean} True if form is valid, false otherwise
   */
  function validateForm(formData) {
    // Clear previous errors
    Object.keys(errors).forEach((key) => delete errors[key]);

    // Validate each field
    const fields = ['username', 'name', 'information_id', 'password1', 'password2'];
    fields.forEach((field) => {
      validateField(field, formData);
    });

    // Return validation result
    return !Object.keys(errors).some((key) => key !== 'general');
  }

  /**
   * Sets errors from server response
   * @param {Object} serverErrors - Error object from server
   */
  function setServerErrors(serverErrors) {
    if (serverErrors) {
      Object.keys(serverErrors).forEach((key) => {
        if (Array.isArray(serverErrors[key])) {
          errors[key] = serverErrors[key][0];
        } else {
          errors[key] = serverErrors[key];
        }
      });
    }
  }

  /**
   * Sets a general error message
   * @param {string} message - The error message to set
   */
  function setGeneralError(message) {
    errors.general = message;
  }

  return {
    errors,
    clearError,
    validateField,
    validateForm,
    setServerErrors,
    setGeneralError,
  };
}
