import { api } from "@/lib/api";

import type {
  ConversationListItem,
  ConversationResponse,
  Message,
  MessageTemplateSummary,
  SendMessageRequest,
  StartConversationRequest,
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

export function getConversations() {
  return api<ConversationListItem[]>(
    "/inbox/conversations",
    {
      accessToken: getAccessToken(),
    },
  );
}

export function getConversation(
  conversationId: string,
) {
  return api<ConversationResponse>(
    `/inbox/conversations/${conversationId}`,
    {
      accessToken: getAccessToken(),
    },
  );
}

export function getConversationMessages(
  conversationId: string,
) {
  return api<Message[]>(
    `/inbox/conversations/${conversationId}/messages`,
    {
      accessToken: getAccessToken(),
    },
  );
}

export function sendConversationMessage(
  conversationId: string,
  payload: SendMessageRequest,
) {
  return api<Message>(
    `/inbox/conversations/${conversationId}/messages`,
    {
      method: "POST",
      accessToken: getAccessToken(),
      body: JSON.stringify(payload),
    },
  );
}

export function getMessageTemplates() {
  return api<MessageTemplateSummary[]>(
    "/inbox/templates",
    {
      accessToken: getAccessToken(),
    },
  );
}

export function startConversation(
  payload: StartConversationRequest,
) {
  return api<ConversationResponse>(
    "/inbox/conversations",
    {
      method: "POST",
      accessToken: getAccessToken(),
      body: JSON.stringify(payload),
    },
  );
}

export function markConversationRead(
  conversationId: string,
) {
  return api<{
    conversation_id: string;
    unread_count: number;
  }>(
    `/inbox/conversations/${conversationId}/read`,
    {
      method: "POST",
      accessToken: getAccessToken(),
    },
  );
}
