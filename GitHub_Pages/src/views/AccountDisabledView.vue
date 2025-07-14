<template>
  <div class="container mt-5 d-flex justify-content-center align-items-center"
       style="min-height: 80vh;">
    <div class="card p-4 shadow-sm" style="max-width: 800px; width: 100%;">
      <h3 class="text-center mb-4">🚫 Account Access Denied</h3>

      <div class="security-warning">
        <h5 :class="alertHeaderClass">{{ securityIcon }} Account Security Alert</h5>
        <p class="text-muted small">
          Access to this account has been restricted for security reasons. All access attempts are logged and monitored.
        </p>
        <div class="log-details">
          <div class="log-entry"><span class="log-separator">--- Account Status Report ---</span></div>
          <div class="log-entry"><span class="log-key">EVENT ID:</span><span class="log-value">{{ eventId }}</span></div>
          <div class="log-entry"><span class="log-key">TIMESTAMP (UTC):</span><span class="log-value">{{ currentTime }}</span></div>
          <div class="log-entry"><span class="log-key">STATUS CODE:</span><span class="log-value">{{ statusCode }}</span></div>
          <div class="log-entry"><span class="log-key">RESTRICTION TYPE:</span><span class="log-value">{{ restrictionType }}</span></div>

          <div class="log-entry"><span class="log-separator">--- Account Details ---</span></div>
          <div class="log-entry"><span class="log-key">USERNAME:</span><span class="log-value">{{ username || 'N/A' }}</span></div>
          <div class="log-entry"><span class="log-key">ACCOUNT STATUS:</span><span class="log-value">{{ accountStatus?.status || 'UNKNOWN' }}</span></div>
          <div class="log-entry"><span class="log-key">FAILED ATTEMPTS:</span><span class="log-value">{{ accountStatus?.failed_attempts || 0 }}</span></div>
          <div v-if="accountStatus?.locked_until" class="log-entry">
            <span class="log-key">LOCKED UNTIL:</span><span class="log-value">{{ formatLockTime(accountStatus.locked_until) }}</span>
          </div>

          <div class="log-entry"><span class="log-separator">--- Session Information ---</span></div>
          <div class="log-entry"><span class="log-key">SESSION ID:</span><span class="log-value">{{ sessionId }}</span></div>
          <div class="log-entry"><span class="log-key">IP ADDRESS:</span><span class="log-value">{{ clientInfo.ip }}</span></div>
          <div class="log-entry"><span class="log-key">USER AGENT:</span><span class="log-value">{{ clientInfo.browser }}</span></div>
          <div class="log-entry"><span class="log-key">LOCATION:</span><span class="log-value">{{ clientInfo.location }}</span></div>

          <div class="log-entry"><span class="log-separator">--- Security Message ---</span></div>
          <div class="log-entry">
            <span class="log-key">REASON:</span>
            <pre class="log-value message-formatted">{{ securityMessage }}</pre>
          </div>
          
          <div v-if="accountStatus?.status === 'locked'" class="log-entry">
            <span class="log-key">NEXT ACTION:</span>
            <span class="log-value">{{ nextActionMessage }}</span>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="action-buttons mt-4">
          <button @click="handleLogout" class="btn btn-primary me-2">
            <i class="fas fa-sign-out-alt me-2"></i>
            Return to Login
          </button>
          <button v-if="canRetry" @click="handleRetry" class="btn btn-secondary">
            <i class="fas fa-redo me-2"></i>
            Retry Access
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { UAParser } from 'ua-parser-js';
import { 
  getCurrentUserStatus, 
  formatLockTime, 
  clearUserData
} from '../utils/userStatus.js';

const router = useRouter();
const currentTime = ref('');
const accountStatus = ref(null);
const eventId = ref('');
const sessionId = ref('');
const username = ref('');
const clientInfo = ref({
  ip: 'Resolving...',
  browser: 'N/A',
  location: 'Resolving...'
});

// Generate unique identifiers
const generateEventId = () => {
  return 'ACC-' + crypto.randomUUID().substring(0, 8).toUpperCase();
};

const generateSessionId = () => {
  return 'SES-' + crypto.randomUUID().substring(0, 12).toUpperCase();
};

// Get account status from utility function
const getUserStatus = () => {
  accountStatus.value = getCurrentUserStatus();
  
  // Try to get username from localStorage
  const userProfile = localStorage.getItem('user_profile');
  if (userProfile) {
    try {
      const profile = JSON.parse(userProfile);
      username.value = profile.name || profile.username || 'Unknown User';
    } catch (error) {
      console.error('Error parsing user profile:', error);
    }
  }
};

// Computed properties for dynamic content
const alertHeaderClass = computed(() => {
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

const securityIcon = computed(() => {
  if (!accountStatus.value) return '⚠️';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return '🔒';
    case 'disabled':
      return '🚫';
    default:
      return '⚠️';
  }
});

const statusCode = computed(() => {
  if (!accountStatus.value) return 'ACC-403-UNKNOWN';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'ACC-423-LOCKED';
    case 'disabled':
      return 'ACC-403-DISABLED';
    default:
      return 'ACC-403-RESTRICTED';
  }
});

const restrictionType = computed(() => {
  if (!accountStatus.value) return 'UNKNOWN_RESTRICTION';
  
  switch (accountStatus.value.status) {
    case 'locked':
      return 'TEMPORARY_LOCK';
    case 'disabled':
      return 'ADMINISTRATIVE_DISABLE';
    default:
      return 'ACCESS_RESTRICTION';
  }
});

const securityMessage = computed(() => {
  if (!accountStatus.value) {
    return "Account access has been restricted.\nContact system administrator for assistance.";
  }
  
  switch (accountStatus.value.status) {
    case 'locked':
      return `Account temporarily locked due to ${accountStatus.value.failed_attempts || 0} failed login attempts.\nLock will expire automatically or contact administrator.`;
    case 'disabled':
      return "Account has been administratively disabled.\nContact system administrator to restore access.";
    default:
      return accountStatus.value.message || "Account access restriction in effect.\nContact administrator for details.";
  }
});

const nextActionMessage = computed(() => {
  if (!accountStatus.value || accountStatus.value.status !== 'locked') return '';
  
  if (accountStatus.value.lock_expired) {
    return 'Lock has expired - retry access available';
  } else if (accountStatus.value.locked_until) {
    return `Wait until ${formatLockTime(accountStatus.value.locked_until)} or contact administrator`;
  } else {
    return 'Contact administrator to unlock account';
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

// Parse client information
const parseClientInfo = () => {
  const parser = new UAParser();
  const result = parser.getResult();
  const browserName = result.browser.name || 'Unknown';
  const browserVersion = result.browser.version || '';
  clientInfo.value.browser = `${browserName} ${browserVersion}`.trim();
};

// Fetch client IP and location
const fetchClientInfo = async () => {
  try {
    const [geoResponse, ipResponse] = await Promise.all([
      fetch('https://api.bigdatacloud.net/data/reverse-geocode-client'),
      fetch('http://ip-api.com/json')
    ]);

    if (geoResponse.ok) {
      const geoData = await geoResponse.json();
      const locationParts = [geoData.city, geoData.principalSubdivision, geoData.countryName].filter(Boolean);
      clientInfo.value.location = locationParts.length > 0 ? locationParts.join(', ') : 'Unavailable';
    }

    if (ipResponse.ok) {
      const ipData = await ipResponse.json();
      clientInfo.value.ip = ipData.query || 'Unavailable';
    }
  } catch (error) {
    console.error('Error fetching client info:', error);
    clientInfo.value.ip = 'Unavailable';
    clientInfo.value.location = 'Unavailable';
  }
};

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

// Set current time and initialize data when component mounts
onMounted(async () => {
  const now = new Date();
  currentTime.value = now.toISOString();
  eventId.value = generateEventId();
  sessionId.value = generateSessionId();
  
  getUserStatus();
  parseClientInfo();
  await fetchClientInfo();
});
</script>

<style scoped>
.security-warning {
  border: 1px solid #dc3545;
  border-radius: 0.25rem;
  padding: 1rem;
  margin-top: 1rem;
  background-color: #f8f9fa;
}

.security-warning h5 {
  font-weight: bold;
}

.log-details {
  background-color: #e9ecef;
  padding: 0.75rem;
  border-radius: 0.25rem;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85em;
  color: #212529;
  margin-bottom: 1rem;
}

.log-entry {
  display: flex;
  line-height: 1.6;
}

.log-key {
  color: #6c757d;
  font-weight: bold;
  flex-shrink: 0;
  width: 160px;
}

.log-value {
  word-break: break-all;
  color: #212529;
}

.log-separator {
  flex-basis: 100%;
  text-align: center;
  color: #adb5bd;
  margin: 0.5rem 0;
  font-weight: bold;
}

.message-formatted {
  margin: 0;
  padding: 0;
  font-family: inherit;
  font-size: inherit;
  white-space: pre-wrap;
  line-height: 1.5;
  background: none;
  border: none;
}

.action-buttons {
  text-align: center;
}

.btn {
  border-radius: 0.25rem;
  padding: 0.5rem 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  border: none;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
  transform: translateY(-1px);
}

.btn-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
  border: none;
}

.btn-secondary:hover {
  background: linear-gradient(135deg, #5a6268 0%, #495057 100%);
  transform: translateY(-1px);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card {
    margin: 1rem;
  }
  
  .log-key {
    width: 140px;
    font-size: 0.8em;
  }
  
  .log-value {
    font-size: 0.8em;
  }
  
  .action-buttons .btn {
    display: block;
    width: 100%;
    margin: 0.25rem 0;
  }
}
</style> 