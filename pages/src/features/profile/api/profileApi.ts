import { apiRequest } from '@shared/api/client';
import type { UserProfile, UserProfileUpdatePayload } from '@profile/types/profile';

export async function getUserProfile() {
  return apiRequest<{ success?: boolean; data: UserProfile }>('/authn/profile/');
}

export async function updateUserProfile(profileData: UserProfileUpdatePayload) {
  return apiRequest<{
    success?: boolean;
    data?: UserProfile;
    errors?: Record<string, string | string[]>;
    message?: string;
  }>('/authn/profile/', {
    method: 'PUT',
    body: profileData,
  });
}
