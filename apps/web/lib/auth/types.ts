export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface RegisterRequest {
  organization_name: string;
  full_name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}