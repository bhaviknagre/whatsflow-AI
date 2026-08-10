import { api } from "@/lib/api";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from "./types";

export function login(
  data: LoginRequest,
) {
  return api<TokenResponse>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function register(
  data: RegisterRequest,
) {
  return api<TokenResponse>(
    "/auth/register",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function refresh() {
  return api<TokenResponse>(
    "/auth/refresh",
    {
      method: "POST",
    },
  );
}

export function logout() {
  return api<{ message: string }>(
    "/auth/logout",
    {
      method: "POST",
    },
  );
}