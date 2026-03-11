import { reactive } from 'vue';

const USER_INFO_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

const state = reactive({
  userInfo: null,
  userInfoTimestamp: 0,
  apiError: null,
});

export function setUserInfo(data) {
  state.userInfo = data;
  state.userInfoTimestamp = Date.now();
}

export function getUserInfo() {
  return state.userInfo;
}

export function clearUserInfo() {
  state.userInfo = null;
  state.userInfoTimestamp = 0;
}

export function isUserInfoStale() {
  return !state.userInfoTimestamp || Date.now() - state.userInfoTimestamp > USER_INFO_CACHE_TTL_MS;
}

export function invalidateUserInfoCache() {
  state.userInfoTimestamp = 0;
}

export function setApiError(error) {
  state.apiError = error;
}

export function getApiError() {
  return state.apiError;
}
