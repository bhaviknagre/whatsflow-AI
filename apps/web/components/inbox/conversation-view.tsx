"use client";

import { MessageComposer } from "./message-composer";

import {
  formatPhoneNumber,
  parseWhatsAppTimestamp,
} from "@/lib/inbox/format";
import type { ConversationResponse } from "@/lib/inbox/types";

type Props = {
  conversation: ConversationResponse | null;
  onSendMessage: (text: string) => Promise<void>;
};


function MessageStatus({
  status,
}: {
  status: string;
}) {
  if (status === "pending") {
    return (
      <span
        className="ml-1 inline-flex items-center"
        aria-label="Sending"
        title="Sending"
      >
        ◷
      </span>
    );
  }

  if (status === "sent") {
    return (
      <span
        className="ml-1 inline-flex items-center"
        aria-label="Sent"
        title="Sent"
      >
        ✓
      </span>
    );
  }

  if (status === "delivered") {
    return (
      <span
        className="ml-1 inline-flex items-center"
        aria-label="Delivered"
        title="Delivered"
      >
        ✓✓
      </span>
    );
  }

  if (status === "read") {
    return (
      <span
        className="ml-1 inline-flex items-center font-semibold text-sky-300"
        aria-label="Read"
        title="Read"
      >
        ✓✓
      </span>
    );
  }

  if (status === "failed") {
    return (
      <span
        className="ml-1 inline-flex items-center font-semibold text-destructive"
        aria-label="Failed"
        title="Failed"
      >
        !
      </span>
    );
  }

  return null;
}

export function ConversationView({
  conversation,
  onSendMessage,
}: Props) {
  if (!conversation) {
    return (
      <section className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">
          Select a conversation
        </p>
      </section>
    );
  }

  return (
    <section className="flex min-w-0 flex-1 flex-col">
      <header className="flex h-[73px] items-center border-b px-6">
        <div>
          <h2 className="font-semibold">
            {formatPhoneNumber(
              conversation.customer_phone_number,
            )}
          </h2>

          <p className="text-xs text-muted-foreground">
            WhatsApp conversation
          </p>
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {conversation.messages.map((message) => {
          const outbound =
            message.direction === "outbound";

          return (
            <div
              key={message.id}
              className={`flex ${
                outbound
                  ? "justify-end"
                  : "justify-start"
              }`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm ${
                  outbound
                    ? "rounded-br-sm bg-primary text-primary-foreground"
                    : "rounded-bl-sm bg-muted"
                }`}
              >
                <p>
                  {message.text ??
                    `[${message.message_type}]`}
                </p>

                <div
                  className={`mt-1 text-[10px] ${
                    outbound
                      ? "text-primary-foreground/70"
                      : "text-muted-foreground"
                  }`}
                >
                  {parseWhatsAppTimestamp(
                    message.created_at,
                  ).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}

                  {outbound && (
                    <MessageStatus
                      status={message.status}
                    />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <MessageComposer
        onSendMessage={onSendMessage}
      />
    </section>
  );
}