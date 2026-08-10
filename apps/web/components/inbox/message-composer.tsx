"use client";

import { useState } from "react";
import { Send } from "lucide-react";

type Props = {
  onSendMessage: (text: string) => Promise<void>;
};

export function MessageComposer({
  onSendMessage,
}: Props) {
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const text = message.trim();

    if (!text || sending) {
      return;
    }

    try {
      setSending(true);

      await onSendMessage(text);

      setMessage("");
    } catch {
      // Error is surfaced via the inbox error banner;
      // keep the draft so the user can retry.
    } finally {
      setSending(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t p-4"
    >
      <div className="flex items-end gap-3">
        <textarea
          value={message}
          onChange={(event) =>
            setMessage(event.target.value)
          }
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey
            ) {
              event.preventDefault();

              void handleSubmit(
                event as unknown as React.FormEvent<HTMLFormElement>,
              );
            }
          }}
          placeholder="Type a message..."
          rows={2}
          disabled={sending}
          className="min-h-[44px] flex-1 resize-none rounded-xl border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary/20"
        />

        <button
          type="submit"
          disabled={
            sending || !message.trim()
          }
          className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Send message"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
}