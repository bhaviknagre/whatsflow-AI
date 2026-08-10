"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getConversation,
  getConversations,
  markConversationRead,
  sendConversationMessage,
} from "@/lib/inbox/api";
import { connectRealtime } from "@/lib/inbox/realtime";
import {
  getLatestMessageStatus,
} from "@/lib/inbox/status";

import type {
  ConversationListItem,
  ConversationResponse,
} from "@/lib/inbox/types";

import { ConversationList } from "./conversation-list";
import { ConversationView } from "./conversation-view";
import { CustomerPanel } from "./customer-panel";
import { NewConversationDialog } from "./new-conversation-dialog";

export function InboxShell() {
  const [conversations, setConversations] =
    useState<ConversationListItem[]>([]);

  const [selectedConversation, setSelectedConversation] =
    useState<ConversationResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isNewConversationOpen, setIsNewConversationOpen] =
    useState(false);

  /*
   * WebSocket callbacks are long-lived and only close
   * over state from when connectRealtime() was first
   * called. A ref lets the handler always read the
   * current selection instead of a stale one.
   */
  const selectedConversationIdRef = useRef<
    string | null
  >(null);

  useEffect(() => {
    selectedConversationIdRef.current =
      selectedConversation?.id ?? null;
  }, [selectedConversation]);

  const selectConversation = useCallback(
    async (conversationId: string) => {
      try {
        setError(null);

        const conversation =
          await getConversation(conversationId);

        setSelectedConversation(conversation);

        if (conversation.unread_count > 0) {
          await markConversationRead(
            conversationId,
          );

          setConversations((current) =>
            current.map((item) =>
              item.id === conversationId
                ? {
                    ...item,
                    unread_count: 0,
                  }
                : item,
            ),
          );
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load conversation.",
        );
      }
    },
    [],
  );

  useEffect(() => {
    async function loadInbox() {
      try {
        setLoading(true);
        setError(null);

        const data = await getConversations();

        setConversations(data);

        if (data.length > 0) {
          await selectConversation(data[0].id);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load inbox.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadInbox();
  }, [selectConversation]);

  /*
   * Real-time updates over WebSocket.
   *
   * Meta sends message status updates to our webhook.
   * The backend updates the database and broadcasts the
   * change to connected clients. This replaces polling:
   *
   * sent -> delivered -> read
   *
   * and new inbound WhatsApp messages both arrive
   * immediately, with no refresh and no interval.
   *
   * The socket reconnects itself on disconnect (network
   * blip, server restart, etc.) with a fixed 2s delay,
   * managed here rather than inside connectRealtime()
   * so a single effect owns the connection's lifecycle.
   */
  useEffect(() => {
    let socket: WebSocket | null = null;

    let reconnectTimer:
      | ReturnType<typeof setTimeout>
      | null = null;

    let stopped = false;
    let reconnectAttempt = 0;

    function connect() {
      if (stopped) {
        return;
      }

      socket = connectRealtime({
        onEvent: (event) => {
          if (event.type === "message_status") {
            setSelectedConversation((current) => {
              if (!current) {
                return current;
              }

              return {
                ...current,
                messages: current.messages.map(
                  (message) =>
                    message.whatsapp_message_id ===
                    event.message_id
                      ? {
                          ...message,
                          status:
                            getLatestMessageStatus(
                              message.status,
                              event.status,
                            ),
                        }
                      : message,
                ),
              };
            });

            setConversations((current) =>
              current.map((conversation) => {
                if (
                  conversation.last_message
                    ?.whatsapp_message_id !==
                  event.message_id
                ) {
                  return conversation;
                }

                const lastMessage =
                  conversation.last_message;

                return {
                  ...conversation,
                  last_message: {
                    ...lastMessage,
                    status:
                      getLatestMessageStatus(
                        lastMessage.status,
                        event.status,
                      ),
                  },
                };
              }),
            );

            return;
          }

          if (event.type === "message_created") {
            const incomingMessage =
              event.message;

            const isSelected =
              selectedConversationIdRef.current ===
              event.conversation_id;

            if (isSelected) {
              setSelectedConversation((current) => {
                if (!current) {
                  return current;
                }

                if (
                  current.messages.some(
                    (message) =>
                      message.whatsapp_message_id ===
                      incomingMessage.whatsapp_message_id,
                  )
                ) {
                  return current;
                }

                return {
                  ...current,
                  messages: [
                    ...current.messages,
                    incomingMessage,
                  ],
                };
              });
            }

            const markRead = isSelected
              ? markConversationRead(
                  event.conversation_id,
                ).catch(() => {
                  // Background failure is handled by
                  // the subsequent conversation refresh.
                })
              : Promise.resolve();

            markRead
              .then(() => getConversations())
              .then(setConversations)
              .catch(() => {
                // Ignore background refresh failures.
              });
          }
        },

        onDisconnect: () => {
          if (stopped) {
            return;
          }

          const delay = Math.min(
            1000 * 2 ** reconnectAttempt,
            30_000,
          );

          reconnectAttempt += 1;

          console.info(
            `[Realtime] reconnecting in ${delay}ms`,
          );

          if (reconnectTimer) {
            clearTimeout(reconnectTimer);
          }

          reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            connect();
          }, delay);
        },
      });

      if (socket) {
        socket.addEventListener(
          "open",
          () => {
            reconnectAttempt = 0;
          },
          { once: true },
        );
      }
    }

    connect();

    return () => {
      stopped = true;

      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      socket?.close();
      socket = null;
    };
  }, []);

  async function handleSendMessage(text: string) {
    if (!selectedConversation) {
      return;
    }

    try {
      setError(null);

      const newMessage = await sendConversationMessage(
        selectedConversation.id,
        { text },
      );

      setSelectedConversation((current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,
          messages: [
            ...current.messages,
            newMessage,
          ],
        };
      });

      setConversations((current) =>
        current.map((conversation) =>
          conversation.id === selectedConversation.id
            ? {
                ...conversation,
                last_message: newMessage,
                updated_at: new Date().toISOString(),
              }
            : conversation,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to send message.",
      );

      throw err;
    }
  }

  function handleConversationStarted(
    conversation: ConversationResponse,
  ) {
    const lastMessage =
      conversation.messages.at(-1) ?? null;

    const listItem: ConversationListItem = {
      id: conversation.id,
      whatsapp_connection_id:
        conversation.whatsapp_connection_id,
      customer_phone_number:
        conversation.customer_phone_number,
      last_message: lastMessage,
      unread_count: conversation.unread_count,
      created_at: conversation.created_at,
      updated_at: conversation.updated_at,
    };

    setConversations((current) => [
      listItem,
      ...current.filter(
        (item) => item.id !== conversation.id,
      ),
    ]);

    setSelectedConversation(conversation);
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">
          Loading inbox...
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full overflow-hidden border bg-background">
      <ConversationList
        conversations={conversations}
        selectedId={
          selectedConversation?.id ?? null
        }
        onSelect={selectConversation}
        onNewConversationClick={() =>
          setIsNewConversationOpen(true)
        }
      />

      <ConversationView
        conversation={selectedConversation}
        onSendMessage={handleSendMessage}
      />

      <CustomerPanel
        conversation={selectedConversation}
      />

      <NewConversationDialog
        open={isNewConversationOpen}
        onOpenChange={setIsNewConversationOpen}
        onConversationStarted={
          handleConversationStarted
        }
      />

      {error && (
        <div className="fixed bottom-4 right-4 z-50 rounded-md border bg-background p-4 text-sm shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}