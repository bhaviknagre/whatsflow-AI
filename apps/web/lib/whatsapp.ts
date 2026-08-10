import { apiFetch } from "./api";

export interface MetaConnectResponse {
  state: string;
}

export interface WhatsAppConnection {
  id: string;
  waba_id: string;
  phone_number_id: string;
  display_phone_number: string | null;
  verified_name: string | null;
  is_active: boolean;
}

export async function getWhatsAppConnectState(
  token: string,
): Promise<MetaConnectResponse> {
  return apiFetch<MetaConnectResponse>(
    "/api/v1/whatsapp/connect",
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
}

export async function getWhatsAppConnections(
  token: string,
): Promise<WhatsAppConnection[]> {
  return apiFetch<WhatsAppConnection[]>(
    "/api/v1/whatsapp/connections",
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
}