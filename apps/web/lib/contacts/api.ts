import { api } from "@/lib/api";

export interface Contact {
  id: string;
  organization_id: string;
  phone_number: string;
  name: string | null;
  profile_name: string | null;
  is_blocked: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateContactRequest {
  phone_number: string;
  name?: string;
}

export interface UpdateContactRequest {
  name?: string | null;
  is_blocked?: boolean;
}

export async function getContacts(
  search?: string,
): Promise<Contact[]> {
  const accessToken =
    typeof window !== "undefined"
      ? window.sessionStorage.getItem("access_token")
      : null;

  const query = search?.trim()
    ? `?search=${encodeURIComponent(search.trim())}`
    : "";

  return api<Contact[]>(
    `/contacts${query}`,
    accessToken
      ? { accessToken }
      : {},
  );
}

export async function createContact(
  data: CreateContactRequest,
): Promise<Contact> {
  const accessToken =
    window.sessionStorage.getItem("access_token");

  if (!accessToken) {
    throw new Error("Please login first.");
  }

  return api<Contact>("/contacts", {
    method: "POST",
    accessToken,
    body: JSON.stringify(data),
  });
}

export async function updateContact(
  contactId: string,
  data: UpdateContactRequest,
): Promise<Contact> {
  const accessToken =
    window.sessionStorage.getItem("access_token");

  if (!accessToken) {
    throw new Error("Please login first.");
  }

  return api<Contact>(`/contacts/${contactId}`, {
    method: "PATCH",
    accessToken,
    body: JSON.stringify(data),
  });
}

export async function deleteContact(
  contactId: string,
): Promise<void> {
  const accessToken =
    window.sessionStorage.getItem("access_token");

  if (!accessToken) {
    throw new Error("Please login first.");
  }

  await api<unknown>(`/contacts/${contactId}`, {
    method: "DELETE",
    accessToken,
  });
}
