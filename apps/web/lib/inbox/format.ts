const EPOCH_SECONDS_PATTERN = /^\d+$/;

export function parseWhatsAppTimestamp(
  value: string,
): Date {
  if (EPOCH_SECONDS_PATTERN.test(value)) {
    return new Date(Number(value) * 1000);
  }

  return new Date(value);
}

const INDIA_DIGITS_PATTERN = /^91\d{10}$/;

export function formatPhoneNumber(
  value: string,
): string {
  const digits = value.replace(/\D/g, "");

  if (INDIA_DIGITS_PATTERN.test(digits)) {
    return `+91 ${digits.slice(2)}`;
  }

  if (digits) {
    return `+${digits}`;
  }

  return value;
}
