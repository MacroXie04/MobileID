import type { Ref } from 'vue';
import type { Router } from 'vue-router';

export interface UserProfile {
  name: string;
  information_id: string;
  user_profile_img?: string | null;
  user_profile_img_base64?: string;
}

export interface UserProfileUpdatePayload {
  name?: string;
  information_id?: string;
  user_profile_img_base64?: string;
  [key: string]: unknown;
}

export interface ProfileFormData {
  name: string;
  information_id: string;
}

export type ProfileErrors = Record<string, string>;

export interface ProfileEditLogicOptions {
  redirectOnSubmit?: boolean;
  redirectPath?: string;
}

export interface ImageCropperOptions {
  targetWidth?: number;
  targetHeight?: number;
  quality?: number;
  enableAdvancedControls?: boolean;
}

export interface ProfileLoadDeps {
  formData: Ref<UserProfile>;
  originalData: Ref<ProfileFormData>;
  avatarPreviewUrl: Ref<string>;
  errors: Ref<ProfileErrors>;
}

export interface ProfileAvatarDeps {
  errors: Ref<ProfileErrors>;
  avatarFile: Ref<File | null>;
  avatarPreviewUrl: Ref<string>;
  triggerAutoSave: () => void;
}

export interface ProfileSubmitDeps {
  formData: Ref<UserProfile>;
  avatarFile: Ref<File | null>;
  errors: Ref<ProfileErrors>;
  successMessage: Ref<string>;
  originalData: Ref<ProfileFormData>;
  loading: Ref<boolean>;
  router: Router;
  redirectOnSubmit: boolean;
  redirectPath: string;
}

export interface ProfileAutoSaveDeps {
  formData: Ref<UserProfile>;
  avatarFile: Ref<File | null>;
  originalData: Ref<ProfileFormData>;
}
