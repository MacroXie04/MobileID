/**
 * User Status Utility Functions
 * Provides helper functions for managing and accessing user account status
 */

import apiClient from '../api.js';

/**
 * Get current user status from localStorage or API
 * @returns {Object|null} User status object or null if not available
 */
export const getCurrentUserStatus = () => {
  try {
    const statusData = localStorage.getItem('user_status');
    if (statusData) {
      return JSON.parse(statusData);
    }
  } catch (error) {
    console.error('Error parsing user status:', error);
  }
  return null;
};

/**
 * Get current user profile from localStorage
 * @returns {Object|null} User profile object or null if not available
 */
export const getCurrentUserProfile = () => {
  try {
    const profileData = localStorage.getItem('user_profile');
    if (profileData) {
      return JSON.parse(profileData);
    }
  } catch (error) {
    console.error('Error parsing user profile:', error);
  }
  return null;
};

/**
 * Check if user account is active
 * @returns {boolean} True if user is active, false otherwise
 */
export const isUserActive = () => {
  const status = getCurrentUserStatus();
  if (!status) return false;
  
  return status.is_active === true && status.status === 'active';
};

/**
 * Check if user account is locked
 * @returns {boolean} True if user is locked, false otherwise
 */
export const isUserLocked = () => {
  const status = getCurrentUserStatus();
  if (!status) return false;
  
  return status.is_locked === true;
};

/**
 * Check if user account is disabled
 * @returns {boolean} True if user is disabled, false otherwise
 */
export const isUserDisabled = () => {
  const status = getCurrentUserStatus();
  if (!status) return false;
  
  return status.status === 'disabled';
};

/**
 * Check if user lock has expired
 * @returns {boolean} True if lock has expired, false otherwise
 */
export const isLockExpired = () => {
  const status = getCurrentUserStatus();
  if (!status) return false;
  
  return status.lock_expired === true;
};

/**
 * Get user status message
 * @returns {string} Human-readable status message
 */
export const getUserStatusMessage = () => {
  const status = getCurrentUserStatus();
  if (!status) return 'Unknown status';
  
  return status.message || 'No status message available';
};

/**
 * Get failed login attempts count
 * @returns {number} Number of failed login attempts
 */
export const getFailedLoginAttempts = () => {
  const status = getCurrentUserStatus();
  if (!status) return 0;
  
  return status.failed_attempts || 0;
};

/**
 * Get lock expiration time
 * @returns {Date|null} Lock expiration date or null if not locked
 */
export const getLockExpirationTime = () => {
  const status = getCurrentUserStatus();
  if (!status || !status.locked_until) return null;
  
  try {
    return new Date(status.locked_until);
  } catch (error) {
    console.error('Error parsing lock time:', error);
    return null;
  }
};

/**
 * Format lock time for display
 * @param {string|Date} lockTime - Lock time to format
 * @returns {string} Formatted lock time string
 */
export const formatLockTime = (lockTime) => {
  if (!lockTime) return 'N/A';
  
  try {
    const date = new Date(lockTime);
    return date.toLocaleString();
  } catch (error) {
    return String(lockTime);
  }
};

/**
 * Refresh user status from API
 * @returns {Promise<Object|null>} Updated user status or null if failed
 */
export const refreshUserStatus = async () => {
  try {
    const response = await apiClient.get('/api/me/');
    
    if (response.status === 200) {
      const userData = response.data;
      
      // Store updated status
      if (userData.account_status) {
        localStorage.setItem('user_status', JSON.stringify(userData.account_status));
      }
      if (userData.userprofile) {
        localStorage.setItem('user_profile', JSON.stringify(userData.userprofile));
      }
      
      return userData.account_status || null;
    }
  } catch (error) {
    console.error('Error refreshing user status:', error);
  }
  
  return null;
};

/**
 * Clear all user data from localStorage
 */
export const clearUserData = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_profile');
  localStorage.removeItem('user_status');
};

/**
 * Get status-specific styling information
 * @returns {Object} Object containing CSS classes and colors for current status
 */
export const getStatusStyling = () => {
  const status = getCurrentUserStatus();
  
  if (!status) {
    return {
      headerClass: 'bg-secondary',
      iconClass: 'fas fa-exclamation-triangle',
      textClass: 'text-secondary',
      alertClass: 'alert-secondary'
    };
  }
  
  switch (status.status) {
    case 'active':
      return {
        headerClass: 'bg-success',
        iconClass: 'fas fa-check-circle',
        textClass: 'text-success',
        alertClass: 'alert-success'
      };
      
    case 'locked':
      return {
        headerClass: 'bg-warning',
        iconClass: 'fas fa-lock',
        textClass: 'text-warning',
        alertClass: 'alert-warning'
      };
      
    case 'disabled':
      return {
        headerClass: 'bg-danger',
        iconClass: 'fas fa-ban',
        textClass: 'text-danger',
        alertClass: 'alert-danger'
      };
      
    case 'lock_expired':
      return {
        headerClass: 'bg-info',
        iconClass: 'fas fa-clock',
        textClass: 'text-info',
        alertClass: 'alert-info'
      };
      
    default:
      return {
        headerClass: 'bg-secondary',
        iconClass: 'fas fa-exclamation-triangle',
        textClass: 'text-secondary',
        alertClass: 'alert-secondary'
      };
  }
};

/**
 * Check if user can retry login (lock expired)
 * @returns {boolean} True if user can retry, false otherwise
 */
export const canRetryLogin = () => {
  const status = getCurrentUserStatus();
  if (!status) return false;
  
  return status.status === 'locked' && status.lock_expired === true;
};

/**
 * Get comprehensive user status summary
 * @returns {Object} Object containing all user status information
 */
export const getUserStatusSummary = () => {
  const status = getCurrentUserStatus();
  const profile = getCurrentUserProfile();
  
  return {
    status: status || { status: 'unknown' },
    profile: profile || {},
    isActive: isUserActive(),
    isLocked: isUserLocked(),
    isDisabled: isUserDisabled(),
    lockExpired: isLockExpired(),
    failedAttempts: getFailedLoginAttempts(),
    lockExpiration: getLockExpirationTime(),
    canRetry: canRetryLogin(),
    message: getUserStatusMessage(),
    styling: getStatusStyling()
  };
}; 