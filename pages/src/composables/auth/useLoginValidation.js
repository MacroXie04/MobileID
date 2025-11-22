import { reactive } from 'vue';

/**
 * Composable for handling login form validation
 * @returns {Object} Validation functions and error state
 */
export function useLoginValidation() {
  const errors = reactive({});

  /**
   * Clears error for a specific field
   * @param {string} field - The field name to clear errors for
   */
  function clearError(field) {
    delete errors[field];
    if (field === 'username' || field === 'password') {
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

    if (field === 'username') {
      if (!formData.username.trim()) {
        errors.username = 'Username is required';
      } else if (formData.username.length < 3) {
        errors.username = 'Username must be at least 3 characters';
      }
    }

    if (field === 'password') {
      if (!formData.password) {
        errors.password = 'Password is required';
      }
    }
  }

  /**
   * Validates the entire form
   * @param {Object} formData - The form data object containing username and password
   * @returns {boolean} True if form is valid, false otherwise
   */
  function validateForm(formData) {
    // Clear all errors
    Object.keys(errors).forEach((key) => delete errors[key]);

    // Validate all fields
    validateField('username', formData);
    validateField('password', formData);

    // Return validation result
    return !errors.username && !errors.password;
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
    setGeneralError,
  };
}
