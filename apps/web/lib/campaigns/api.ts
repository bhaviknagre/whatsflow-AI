import { api } from "@/lib/api";

import type {
  Campaign,
  CampaignDetail,
  CreateCampaignRequest,
} from "./types";

function getAccessToken(): string | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }

  return (
    window.sessionStorage.getItem("access_token") ??
    undefined
  );
}

export function getCampaigns() {
  return api<Campaign[]>("/campaigns", {
    accessToken: getAccessToken(),
  });
}

export function getCampaign(campaignId: string) {
  return api<CampaignDetail>(
    `/campaigns/${campaignId}`,
    {
      accessToken: getAccessToken(),
    },
  );
}

export function createCampaign(
  payload: CreateCampaignRequest,
) {
  return api<CampaignDetail>("/campaigns", {
    method: "POST",
    accessToken: getAccessToken(),
    body: JSON.stringify(payload),
  });
}

export function sendCampaign(campaignId: string) {
  return api<CampaignDetail>(
    `/campaigns/${campaignId}/send`,
    {
      method: "POST",
      accessToken: getAccessToken(),
    },
  );
}

export function cancelCampaign(campaignId: string) {
  return api<CampaignDetail>(
    `/campaigns/${campaignId}/cancel`,
    {
      method: "POST",
      accessToken: getAccessToken(),
    },
  );
}
