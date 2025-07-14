<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card shadow" style="max-width: 700px; width: 100%; border-radius: 15px; border: none;">
      <!-- Card Header -->
      <div class="card-header text-white text-center" 
           :style="headerStyle"
           style="border-radius: 15px 15px 0 0;">
        <h4 class="mb-0">
          <i :class="headerIcon" class="me-2"></i>
          {{ headerTitle }}
        </h4>
      </div>

      <!-- Card Body -->
      <div class="card-body text-center p-4">
        <!-- Status Icon -->
        <div class="mb-4">
          <i :class="statusIcon" :style="iconStyle"></i>
        </div>
        
        <!-- Main Message -->
        <h5 class="card-title mb-3" :class="titleClass">{{ mainMessage }}</h5>
        
        <!-- Status Details -->
        <div v-if="accountStatus" class="status-details mb-4">
          <div class="alert" :class="alertClass" role="alert" style="border-radius: 10px; border: none;">
            <div class="row">
              <div class="col-md-6 text-start">
                <strong>Status:</strong> {{ accountStatus.status }}
              </div>
              <div class="col-md-6 text-start">
                <strong>Failed Attempts:</strong> {{ accountStatus.failed_attempts }}
              </div>
            </div>
            <div v-if="accountStatus.locked_until" class="row mt-2">
              <div class="col-12 text-start">
                <strong>Locked Until:</strong> {{ formatLockTime(accountStatus.locked_until) }}
              </div>
            </div>
            <div class="row mt-2">
              <div class="col-12 text-start">
                <strong>Message:</strong> {{ accountStatus.message }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Description -->
        <p class="card-text text-muted mb-4">
          {{ description }}
        </p>
        
        <!-- Action Buttons -->
        <div class="d-grid gap-2 d-md-flex justify-content-md-center">
          <button @click="handleLogout" class="btn btn-primary me-2" 
                  style="border-radius: 25px; padding: 10px 30px; font-weight: 500; transition: all 0.3s ease;">
            <i class="fas fa-sign-out-alt me-2"></i>
            Logout
          </button>
          <button v-if="canRetry" @click="handleRetry" class="btn btn-secondary" 
                  style="border-radius: 25px; padding: 10px 30px; font-weight: 500; transition: all 0.3s ease;">
            <i class="fas fa-redo me-2"></i>
            Try Again
          </button>
        </div>
      </div>
      
      <!-- Card Footer -->
      <div class="card-footer text-center text-muted">
        <small>
          <i class="fas fa-clock me-1"></i>
          Page generated at: {{ currentTime }}
        </small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { 
  getCurrentUserStatus, 
  formatLockTime, 
  clearUserData,
  getStatusStyling 
} from '../utils/userStatus.js';

const router = useRouter();
const currentTime = ref('');
const accountStatus = ref(null);

// Get account status from utility function
const getUserStatus = () => {
  accountStatus.value = getCurrentUserStatus();
};

// Computed properties for dynamic styling and content
const headerStyle = computed(() => {
  if (!accountStatus.value) return 'background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);';
    case 'disabled':
      return 'background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);';
    default:
      return 'background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);';
  }
});

const headerIcon = computed(() => {
  if (!accountStatus.value) return 'fas fa-ban';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'fas fa-lock';
    case 'disabled':
      return 'fas fa-ban';
    default:
      return 'fas fa-exclamation-triangle';
  }
});

const headerTitle = computed(() => {
  if (!accountStatus.value) return 'Account Disabled';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'Account Locked';
    case 'disabled':
      return 'Account Disabled';
    default:
      return 'Account Issue';
  }
});

const statusIcon = computed(() => {
  if (!accountStatus.value) return 'fas fa-exclamation-triangle text-warning';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'fas fa-lock text-warning';
    case 'disabled':
      return 'fas fa-ban text-danger';
    default:
      return 'fas fa-exclamation-triangle text-warning';
  }
});

const iconStyle = computed(() => {
  return { fontSize: '4rem' };
});

const titleClass = computed(() => {
  if (!accountStatus.value) return 'text-danger';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'text-warning';
    case 'disabled':
      return 'text-danger';
    default:
      return 'text-warning';
  }
});

const mainMessage = computed(() => {
  if (!accountStatus.value) return 'Your account is currently disabled';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'Your account is currently locked';
    case 'disabled':
      return 'Your account is currently disabled';
    default:
      return 'There is an issue with your account';
  }
});

const description = computed(() => {
  if (!accountStatus.value) {
    return "We're sorry, but your account is currently disabled and you cannot access system features. Please contact an administrator for more information.";
  }
  
  switch (accountStatus.value.status) {
    case 'locked':
      return "Your account has been temporarily locked due to multiple failed login attempts. Please wait for the lock to expire or contact an administrator for assistance.";
    case 'disabled':
      return "We're sorry, but your account is currently disabled and you cannot access system features. Please contact an administrator for more information.";
    default:
      return "There is an issue with your account status. Please contact an administrator for assistance.";
  }
});

const alertClass = computed(() => {
  if (!accountStatus.value) return 'alert-info';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'alert-warning';
    case 'disabled':
      return 'alert-danger';
    default:
      return 'alert-info';
  }
});

const canRetry = computed(() => {
  if (!accountStatus.value) return false;
  
  // Allow retry if lock has expired
  if (accountStatus.value.status === 'locked' && accountStatus.value.lock_expired) {
    return true;
  }
  
  return false;
});

// Handle logout action
const handleLogout = () => {
  // Clear all stored tokens and user data using utility function
  clearUserData();
  
  // Redirect to login page
  router.push('/login');
};

// Handle retry action
const handleRetry = () => {
  // Clear cached status and redirect to home
  localStorage.removeItem('user_status');
  router.push('/');
};

// Set current time when component mounts
onMounted(() => {
  const now = new Date();
  currentTime.value = now.toLocaleString();
  getUserStatus();
});

// Add hover effect for buttons
const addHoverEffect = () => {
  const buttons = document.querySelectorAll('.btn');
  buttons.forEach(button => {
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
    });
    
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = 'none';
    });
  });
};

onMounted(() => {
  addHoverEffect();
});
</script>

<style scoped>
/* Custom styles for the account disabled page */
.card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-primary {
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  border: none;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
}

.btn-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
  border: none;
}

.btn-secondary:hover {
  background: linear-gradient(135deg, #5a6268 0%, #495057 100%);
}

.alert {
  background-color: #d1ecf1;
  color: #0c5460;
}

.alert-warning {
  background-color: #fff3cd;
  color: #856404;
}

.alert-danger {
  background-color: #f8d7da;
  color: #721c24;
}

.fas {
  font-size: 1.1em;
}

.status-details {
  text-align: left;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card {
    margin: 1rem;
  }
  
  .card-body {
    padding: 1.5rem;
  }
  
  .status-details .row {
    margin: 0;
  }
  
  .status-details .col-md-6,
  .status-details .col-12 {
    padding: 0.25rem 0;
  }
}
</style> 