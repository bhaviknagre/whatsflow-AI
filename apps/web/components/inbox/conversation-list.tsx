"use client";

import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  formatPhoneNumber,
  parseWhatsAppTimestamp,
} from "@/lib/inbox/format";
import type { ConversationListItem } from "@/lib/inbox/types";

type Props = {
  conversations: ConversationListItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNewConversationClick: () => void;
};

export function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onNewConversationClick,
}: Props) {
  return (
    <aside className="flex w-[320px] flex-col border-r">
      <div className="border-b p-4">
        <div className="mb-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">
            Inbox
          </h1>

          <div className="flex items-center gap-2">
            <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
              {conversations.length}
            </span>

            <Button
              type="button"
              variant="outline"
              size="icon-sm"
              aria-label="New conversation"
              onClick={onNewConversationClick}
            >
              <Plus />
            </Button>
          </div>
        </div>

        <input
          type="search"
          placeholder="Search conversations..."
          className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">
            No conversations yet.
          </p>
        ) : (
          conversations.map((conversation) => {
            const selected =
              conversation.id === selectedId;

            const lastMessage =
              conversation.last_message;

            return (
              <button
                key={conversation.id}
                type="button"
                onClick={() =>
                  onSelect(conversation.id)
                }
                className={`w-full border-b p-4 text-left transition ${
                  selected
                    ? "bg-muted"
                    : "hover:bg-muted/50"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 font-semibold text-primary">
                      {conversation.customer_phone_number
                        .slice(-2)
                        .toUpperCase()}
                    </div>

                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">
                        {formatPhoneNumber(
                          conversation.customer_phone_number,
                        )}
                      </p>

                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        {lastMessage?.text ??
                          (lastMessage
                            ? `[${lastMessage.message_type}]`
                            : "No messages yet")}
                      </p>
                    </div>
                  </div>

                  <div className="shrink-0 text-right">
                    <p className="text-[11px] text-muted-foreground">
                      {lastMessage
                        ? parseWhatsAppTimestamp(
                            conversation.updated_at,
                          ).toLocaleTimeString(
                            [],
                            {
                              hour: "2-digit",
                              minute: "2-digit",
                            },
                          )
                        : ""}
                    </p>

                    {conversation.unread_count >
                      0 && (
                      <span className="mt-1 inline-flex min-w-5 items-center justify-center rounded-full bg-primary px-1.5 py-0.5 text-[10px] font-semibold text-primary-foreground">
                        {conversation.unread_count >
                        99
                          ? "99+"
                          : conversation.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}