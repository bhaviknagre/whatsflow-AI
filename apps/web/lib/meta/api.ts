import { api } from "@/lib/api";

export interface MetaConnectResponse {
  state: string;
}

export function connectWhatsApp(accessToken: string) {
  return api<MetaConnectResponse>(
    "/meta/whatsapp/connect",
    {
      method: "GET",
      accessToken,
    },
  );
}
