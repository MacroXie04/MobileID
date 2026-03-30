import { onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { login, userInfo } from '@shared/api/auth.js';
import { ApiError } from '@shared/api/client.js';
import { setUserInfo } from '@shared/state/authState';
import { useLoginValidation } from '@auth/composables/useLoginValidation.js';

export function useLoginLogic() {
  const router = useRouter();
  const route = useRoute();
  const formData = reactive({ username: '', password: '' });
  const loading = ref(false);
  const showPassword = ref(false);
  const registrationSuccess = ref(route.query.registered === 'true');

  // Template refs
  const iconBtn = ref(null);
  const submitBtn = ref(null);

  // Use validation composable
  const {
    errors,
    clearError,
    validateField: validateSingleField,
    validateForm,
    setGeneralError,
  } = useLoginValidation();

  // Setup DOM elements on mounted
  onMounted(() => {
    if (iconBtn.value) {
      const internalBtn = iconBtn.value.shadowRoot?.querySelector('button');
      if (internalBtn) {
        internalBtn.id = 'password-toggle';
        internalBtn.type = 'button';
      }
    }
    if (submitBtn.value) {
      const internalBtn = submitBtn.value.shadowRoot?.querySelector('button');
      if (internalBtn) internalBtn.id = 'login-submit';
    }
  });

  // Wrapper function to pass formData to validation
  function validateField(field) {
    validateSingleField(field, formData);
  }

  async function handleSubmit() {
    if (!validateForm(formData)) return;
    loading.value = true;
    try {
      const res = await login(formData.username, formData.password);
      if (res.message === 'Login successful') {
        // Verify session establishment before redirecting
        const user = await userInfo();
        if (user) {
          setUserInfo(user);
          await router.push('/');
        } else {
          setGeneralError(
            'Login successful but session could not be established. Please check your cookie settings.'
          );
        }
      } else {
        setGeneralError('Unable to sign in. Please try again.');
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err instanceof ApiError) {
        setGeneralError(err.data?.detail || 'Invalid username or password.');
      } else {
        setGeneralError('Network error. Please check your connection and try again.');
      }
    } finally {
      loading.value = false;
    }
  }

  return {
    formData,
    loading,
    showPassword,
    registrationSuccess,
    iconBtn,
    submitBtn,
    errors,
    clearError,
    validateField,
    handleSubmit,
  };
}
