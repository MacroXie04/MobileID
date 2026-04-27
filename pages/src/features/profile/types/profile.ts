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
