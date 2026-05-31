import type { UserProfile } from '@profile';

// Canonical definition lives in the domain-neutral shared layer; re-exported here
// so `@auth` consumers keep importing `ApiErrorData` from the auth barrel.
export type { ApiErrorData } from '@shared/api/client';

export interface AuthUser {
  id?: number | string;
  username?: string;
  email?: string;
  is_activated?: boolean;
  profile?: UserProfile;
  [key: string]: unknown;
}

export interface LoginResponse {
  message?: string;
  success?: boolean;
}

export interface RegisterPayload {
  username?: string;
  name?: string;
  password1?: string;
  password2?: string;
  user_profile_img_base64?: string;
  [key: string]: unknown;
}

export interface RegisterResponse {
  success?: boolean;
  detail?: string;
  message?: string;
  errors?: Record<string, string | string[]>;
}
