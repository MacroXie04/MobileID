<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card shadow" style="max-width: 600px; width: 100%; border-radius: 15px; border: none;">
      <!-- Card Header -->
      <div class="card-header bg-danger text-white text-center" 
           style="border-radius: 15px 15px 0 0; background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
        <h4 class="mb-0">
          <i class="fas fa-ban me-2"></i>
          Account Disabled
        </h4>
      </div>

      <!-- Card Body -->
      <div class="card-body text-center p-4">
        <!-- Warning Icon -->
        <div class="mb-4">
          <i class="fas fa-exclamation-triangle text-warning" style="font-size: 4rem;"></i>
        </div>
        
        <!-- Main Message -->
        <h5 class="card-title text-danger mb-3">Your account is currently disabled</h5>
        
        <!-- Description -->
        <p class="card-text text-muted mb-4">
          We're sorry, but your account is currently disabled and you cannot access system features.
          <br>
          Please contact an administrator for more information.
        </p>
        
        <!-- Info Alert -->
        <div class="alert alert-info" role="alert" style="border-radius: 10px; border: none;">
          <i class="fas fa-info-circle me-2"></i>
          <strong>Note:</strong> If you believe this is an error, please contact the system administrator.
        </div>
        
        <!-- Action Buttons -->
        <div class="d-grid gap-2 d-md-flex justify-content-md-center">
          <button @click="handleLogout" class="btn btn-primary" 
                  style="border-radius: 25px; padding: 10px 30px; font-weight: 500; transition: all 0.3s ease;">
            <i class="fas fa-sign-out-alt me-2"></i>
            Logout
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
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const currentTime = ref('');

// Handle logout action
const handleLogout = () => {
  // Clear all stored tokens and user data
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_profile');
  
  // Redirect to login page
  router.push('/login');
};

// Set current time when component mounts
onMounted(() => {
  const now = new Date();
  currentTime.value = now.toLocaleString();
});

// Add hover effect for button
const addHoverEffect = () => {
  const button = document.querySelector('.btn-primary');
  if (button) {
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 4px 8px rgba(0, 123, 255, 0.3)';
    });
    
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = 'none';
    });
  }
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

.alert {
  background-color: #d1ecf1;
  color: #0c5460;
}

.fas {
  font-size: 1.1em;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card {
    margin: 1rem;
  }
  
  .card-body {
    padding: 1.5rem;
  }
}
</style> 