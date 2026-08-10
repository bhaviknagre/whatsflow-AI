"use client";

import { formatPhoneNumber } from "@/lib/inbox/format";
import type { ConversationResponse } from "@/lib/inbox/types";

type Props = {
  conversation: ConversationResponse | null;
};

export function CustomerPanel({
  conversation,
}: Props) {
  if (!conversation) {
    return (
      <aside className="hidden w-[300px] border-l lg:block">
        <div className="flex h-full items-center justify-center p-6">
          <p className="text-sm text-muted-foreground">
            Customer details
          </p>
        </div>
      </aside>
    );
  }

  const connection =
    conversation.whatsapp_connection;

  return (
    <aside className="hidden w-[300px] overflow-y-auto border-l lg:block">
      <div className="border-b p-6">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-xl font-semibold text-primary">
          {conversation.customer_phone_number
            .slice(-2)}
        </div>

        <h2 className="mt-4 text-center font-semibold">
          {formatPhoneNumber(
            conversation.customer_phone_number,
          )}
        </h2>

        <p className="mt-1 text-center text-xs text-muted-foreground">
          WhatsApp customer
        </p>
      </div>

      <div className="space-y-6 p-5">
        <section>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Customer
          </h3>

          <div className="space-y-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground">
                Phone number
              </p>

              <p className="mt-1 font-medium">
                {formatPhoneNumber(
                  conversation.customer_phone_number,
                )}
              </p>
            </div>
          </div>
        </section>

        <section>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            WhatsApp connection
          </h3>

          <div className="space-y-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground">
                Business name
              </p>

              <p className="mt-1 font-medium">
                {connection.verified_name ??
                  "Not available"}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                WhatsApp number
              </p>

              <p className="mt-1 font-medium">
                {connection.display_phone_number ??
                  "Not available"}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                Connection status
              </p>

              <div className="mt-1 flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${
                    connection.is_active
                      ? "bg-green-500"
                      : "bg-red-500"
                  }`}
                />

                <span>
                  {connection.is_active
                    ? "Active"
                    : "Inactive"}
                </span>
              </div>
            </div>
          </div>
        </section>

        <section>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            WhatsApp identifiers
          </h3>

          <div className="space-y-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground">
                Phone Number ID
              </p>

              <p className="mt-1 break-all font-mono text-xs">
                {connection.phone_number_id}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">
                WABA ID
              </p>

              <p className="mt-1 break-all font-mono text-xs">
                {connection.waba_id}
              </p>
            </div>
          </div>
        </section>
      </div>
    </aside>
  );
}