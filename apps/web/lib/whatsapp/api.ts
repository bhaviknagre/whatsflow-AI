import { api } from "@/lib/api";

export interface WhatsAppConnection {
  id: string;
  waba_id: string;
  phone_number_id: string;
  display_phone_number: string | null;
  verified_name: string | null;
  is_active: boolean;
}

export function getWhatsAppConnections(
  accessToken: string,
) {
  return api<WhatsAppConnection[]>(
    "/whatsapp/connections",
    {
      method: "GET",
      accessToken,
    },
  );
}