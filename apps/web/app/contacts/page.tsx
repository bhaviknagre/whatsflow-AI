"use client";

import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import {
  Contact,
  createContact,
  getContacts,
  updateContact,
} from "@/lib/contacts/api";

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  const loadContacts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await getContacts(search);
      setContacts(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load contacts",
      );
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadContacts();
    }, 250);

    return () => window.clearTimeout(timer);
  }, [loadContacts]);

  async function handleCreate() {
    if (!phone.trim()) {
      return;
    }

    try {
      setSaving(true);
      setError(null);

      await createContact({
        phone_number: phone,
        name: name || undefined,
      });

      setPhone("");
      setName("");
      setShowCreate(false);

      await loadContacts();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create contact",
      );
    } finally {
      setSaving(false);
    }
  }

  async function toggleBlocked(contact: Contact) {
    try {
      await updateContact(contact.id, {
        is_blocked: !contact.is_blocked,
      });

      setContacts((current) =>
        current.map((item) =>
          item.id === contact.id
            ? {
                ...item,
                is_blocked: !item.is_blocked,
              }
            : item,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update contact",
      );
    }
  }

  return (
    <AppShell>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              Contacts
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              Manage your WhatsApp customers and contacts.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            Add contact
          </button>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="rounded-xl border bg-white">
          <div className="border-b p-4">
            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search name or phone number..."
              className="w-full rounded-lg border px-3 py-2 text-sm outline-none focus:border-gray-400"
            />
          </div>

          {loading ? (
            <div className="p-8 text-center text-sm text-gray-500">
              Loading contacts...
            </div>
          ) : contacts.length === 0 ? (
            <div className="p-12 text-center">
              <p className="font-medium text-gray-900">
                No contacts found
              </p>

              <p className="mt-1 text-sm text-gray-500">
                Contacts will also be created automatically
                when customers message you on WhatsApp.
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {contacts.map((contact) => (
                <div
                  key={contact.id}
                  className="flex items-center justify-between p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100 text-sm font-semibold">
                      {(contact.name ||
                        contact.profile_name ||
                        contact.phone_number)
                        .slice(0, 1)
                        .toUpperCase()}
                    </div>

                    <div>
                      <p className="font-medium text-gray-900">
                        {contact.name ||
                          contact.profile_name ||
                          "Unknown contact"}
                      </p>

                      <p className="text-sm text-gray-500">
                        +{contact.phone_number}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {contact.is_blocked && (
                      <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-700">
                        Blocked
                      </span>
                    )}

                    <button
                      type="button"
                      onClick={() =>
                        void toggleBlocked(contact)
                      }
                      className="rounded-lg border px-3 py-1.5 text-xs font-medium hover:bg-gray-50"
                    >
                      {contact.is_blocked
                        ? "Unblock"
                        : "Block"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
              <h2 className="text-lg font-semibold">
                Add contact
              </h2>

              <div className="mt-5 space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Phone number
                  </label>

                  <input
                    value={phone}
                    onChange={(event) =>
                      setPhone(event.target.value)
                    }
                    placeholder="919876543210"
                    className="w-full rounded-lg border px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Name
                  </label>

                  <input
                    value={name}
                    onChange={(event) =>
                      setName(event.target.value)
                    }
                    placeholder="Customer name"
                    className="w-full rounded-lg border px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg border px-4 py-2 text-sm"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  disabled={saving || !phone.trim()}
                  onClick={() => void handleCreate()}
                  className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Create contact"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}