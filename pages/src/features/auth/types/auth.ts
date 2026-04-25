import type { UserProfile } from '@profile';

export interface AuthUser {
  id?: number | string;
  username?: string;
  email?: string;
  is_activated?: boolean;
  profile?: UserProfile;
  [key: string]: unknown;
}

export interface ApiErrorData {
  detail?: string;
  message?: string;
  errors?: Record<string, string | string[]>;
  non_field_errors?: string | string[];
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
