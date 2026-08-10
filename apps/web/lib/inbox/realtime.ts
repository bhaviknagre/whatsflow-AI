export type RealtimeMessage = {
  id: string;
  conversation_id: string;
  whatsapp_message_id: string | null;
  direction: string;
  message_type: string;
  text: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type RealtimeEvent =
  | {
      type: "message_status";
      message_id: string;
      conversation_id: string;
      status: string;
    }
  | {
      type: "message_created";
      conversation_id: string;
      message: RealtimeMessage;
    };

type Options = {
  onEvent: (event: RealtimeEvent) => void;
  onDisconnect?: () => void;
};

function isRealtimeEvent(value: unknown): value is RealtimeEvent {
  if (!value || typeof value !== "object") {
    return false;
  }

  const event = value as Record<string, unknown>;

  if (
    event.type === "message_status"
  ) {
    return (
      typeof event.message_id === "string" &&
      typeof event.conversation_id === "string" &&
      typeof event.status === "string"
    );
  }

  if (
    event.type === "message_created"
  ) {
    const message = event.message;

    if (
      !message ||
      typeof message !== "object"
    ) {
      return false;
    }

    const messageData =
      message as Record<string, unknown>;

    return (
      typeof event.conversation_id === "string" &&
      typeof messageData.id === "string" &&
      typeof messageData.conversation_id === "string" &&
      typeof messageData.direction === "string" &&
      typeof messageData.message_type === "string" &&
      typeof messageData.status === "string"
    );
  }

  return false;
}

function getWebSocketUrl(): string | null {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  if (!apiUrl) {
    console.warn(
      "[Realtime] NEXT_PUBLIC_API_URL is not configured",
    );

    return null;
  }

  try {
    const url = new URL(apiUrl);

    const protocol =
      url.protocol === "https:" ? "wss:" : "ws:";

    return `${protocol}//${url.host}${url.pathname.replace(
      /\/$/,
      "",
    )}/realtime/ws`;
  } catch {
    console.warn(
      "[Realtime] Invalid NEXT_PUBLIC_API_URL",
    );

    return null;
  }
}

export function connectRealtime({
  onEvent,
  onDisconnect,
}: Options): WebSocket | null {
  const token =
    window.sessionStorage.getItem(
      "access_token",
    );

  if (!token) {
    return null;
  }

  const websocketUrl = getWebSocketUrl();

  if (!websocketUrl) {
    return null;
  }

  const socket = new WebSocket(
    `${websocketUrl}?token=${encodeURIComponent(token)}`,
  );

  let heartbeat:
    ReturnType<typeof setInterval> | null =
    null;

  socket.onopen = () => {
    console.info("[Realtime] connected");

    heartbeat = setInterval(() => {
      if (
        socket.readyState ===
        WebSocket.OPEN
      ) {
        socket.send("ping");
      }
    }, 25_000);
  };

  socket.onmessage = (event) => {
    if (event.data === "pong") {
      return;
    }

    try {
      const parsed: unknown =
        JSON.parse(event.data);

      if (!isRealtimeEvent(parsed)) {
        console.warn(
          "[Realtime] ignored invalid event",
        );
        return;
      }

      onEvent(parsed);
    } catch {
      console.warn(
        "[Realtime] invalid JSON event",
      );
    }
  };

  socket.onerror = () => {
    console.warn(
      "[Realtime] socket error",
    );
  };

  socket.onclose = () => {
    if (heartbeat !== null) {
      clearInterval(heartbeat);
      heartbeat = null;
    }

    console.info(
      "[Realtime] disconnected",
    );

    onDisconnect?.();
  };

  return socket;
}