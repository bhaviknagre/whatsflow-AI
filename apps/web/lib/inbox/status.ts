export type MessageStatus =
  | "pending"
  | "sent"
  | "delivered"
  | "read"
  | "failed"
  | string;

const STATUS_RANK: Record<string, number> = {
  pending: 0,
  sent: 1,
  delivered: 2,
  read: 3,
};

export function getLatestMessageStatus(
  current: string,
  incoming: string,
): string {
  if (incoming === "failed") {
    return "failed";
  }

  if (current === "failed") {
    return current;
  }

  const currentRank =
    STATUS_RANK[current] ?? 0;

  const incomingRank =
    STATUS_RANK[incoming] ?? 0;

  return incomingRank >= currentRank
    ? incoming
    : current;
}