"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import {
  createCampaign,
  getCampaigns,
  sendCampaign,
} from "@/lib/campaigns/api";
import type { Campaign } from "@/lib/campaigns/types";
import { getMessageTemplates } from "@/lib/inbox/api";
import type { MessageTemplateSummary } from "@/lib/inbox/types";
import {
  Contact,
  getContacts,
} from "@/lib/contacts/api";

function statusClasses(status: string) {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-700";

    case "running":
      return "bg-blue-100 text-blue-700";

    case "scheduled":
      return "bg-purple-100 text-purple-700";

    case "failed":
      return "bg-red-100 text-red-700";

    case "cancelled":
      return "bg-gray-100 text-gray-700";

    default:
      return "bg-yellow-100 text-yellow-700";
  }
}

function formatDate(value: string | null) {
  if (!value) return "—";

  return new Date(value).toLocaleString();
}

export default function Page() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [templates, setTemplates] = useState<
    MessageTemplateSummary[]
  >([]);

  const [contacts, setContacts] = useState<Contact[]>(
    [],
  );

  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadCampaigns() {
    try {
      setLoading(true);
      setError(null);

      const data = await getCampaigns();

      setCampaigns(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load campaigns.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadTemplates() {
    try {
      const data = await getMessageTemplates();

      setTemplates(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load templates.",
      );
    }
  }

  async function loadContacts() {
    try {
      const data = await getContacts();
      setContacts(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load contacts.",
      );
    }
  }

  useEffect(() => {
    async function load() {
      await Promise.all([
        loadCampaigns(),
        loadTemplates(),
        loadContacts(),
      ]);
    }

    void load();
  }, []);

  async function handleSend(campaignId: string) {
    try {
      setError(null);

      await sendCampaign(campaignId);

      await loadCampaigns();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to send campaign.",
      );
    }
  }

  async function handleCreated() {
    setShowCreate(false);
    await loadCampaigns();
  }

  return (
    <AppShell>
      <div className="space-y-6 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">
              Campaigns
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              Create, send and monitor your WhatsApp campaigns.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90"
          >
            Create campaign
          </button>
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="rounded-xl border bg-background p-8 text-center text-sm text-muted-foreground">
            Loading campaigns...
          </div>
        ) : campaigns.length === 0 ? (
          <div className="rounded-xl border bg-background p-12 text-center">
            <h2 className="text-lg font-medium">
              No campaigns yet
            </h2>

            <p className="mt-2 text-sm text-muted-foreground">
              Create your first WhatsApp campaign to reach
              multiple customers.
            </p>

            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="mt-5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            >
              Create your first campaign
            </button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border bg-background">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/40">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">
                      Campaign
                    </th>

                    <th className="px-4 py-3 text-left font-medium">
                      Template
                    </th>

                    <th className="px-4 py-3 text-left font-medium">
                      Status
                    </th>

                    <th className="px-4 py-3 text-left font-medium">
                      Recipients
                    </th>

                    <th className="px-4 py-3 text-left font-medium">
                      Delivered
                    </th>

                    <th className="px-4 py-3 text-left font-medium">
                      Read
                    </th>

                    <th className="px-4 py-3 text-left font-medium">
                      Failed
                    </th>

                    <th className="px-4 py-3 text-left font-medium">
                      Created
                    </th>

                    <th className="px-4 py-3 text-right font-medium">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {campaigns.map((campaign) => (
                    <tr
                      key={campaign.id}
                      className="border-b last:border-0"
                    >
                      <td className="px-4 py-4">
                        <div className="font-medium">
                          {campaign.name}
                        </div>

                        <div className="mt-1 text-xs text-muted-foreground">
                          {campaign.language_code}
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        {campaign.template_name}
                      </td>

                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ${statusClasses(
                            campaign.status,
                          )}`}
                        >
                          {campaign.status}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        {campaign.total_recipients}
                      </td>

                      <td className="px-4 py-4">
                        {campaign.delivered_count}
                      </td>

                      <td className="px-4 py-4">
                        {campaign.read_count}
                      </td>

                      <td className="px-4 py-4">
                        {campaign.failed_count}
                      </td>

                      <td className="px-4 py-4 text-muted-foreground">
                        {formatDate(campaign.created_at)}
                      </td>

                      <td className="px-4 py-4 text-right">
                        {campaign.status === "draft" ||
                        campaign.status === "scheduled" ? (
                          <button
                            type="button"
                            onClick={() =>
                              void handleSend(campaign.id)
                            }
                            className="rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted"
                          >
                            Send
                          </button>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            —
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {showCreate && (
          <CreateCampaignDialog
            templates={templates}
            contacts={contacts}
            onClose={() => setShowCreate(false)}
            onCreated={handleCreated}
            onError={setError}
          />
        )}
      </div>
    </AppShell>
  );
}

function CreateCampaignDialog({
  templates,
  contacts,
  onClose,
  onCreated,
  onError,
}: {
  templates: MessageTemplateSummary[];
  contacts: Contact[];
  onClose: () => void;
  onCreated: () => Promise<void>;
  onError: (message: string | null) => void;
}) {
  const [name, setName] = useState("");
  const [templateName, setTemplateName] = useState("");
  const [selectedContactIds, setSelectedContactIds] =
    useState<string[]>([]);
  const [parameters, setParameters] = useState<string[]>([]);
  const [scheduledAt, setScheduledAt] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const selectedTemplate = templates.find(
    (template) => template.name === templateName,
  );

  function handleTemplateChange(value: string) {
    setTemplateName(value);

    const template = templates.find(
      (item) => item.name === value,
    );

    setParameters(
      Array(template?.placeholder_count ?? 0).fill(""),
    );
  }

  function toggleContact(contactId: string) {
    setSelectedContactIds((current) =>
      current.includes(contactId)
        ? current.filter(
            (id) => id !== contactId,
          )
        : [...current, contactId],
    );
  }

  function updateParameter(
    index: number,
    value: string,
  ) {
    setParameters((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index ? value : item,
      ),
    );
  }

  function renderPreview() {
    if (!selectedTemplate?.body_text) {
      return "";
    }

    return parameters.reduce(
      (text, value, index) =>
        text.replaceAll(
          `{{${index + 1}}}`,
          value || `{{${index + 1}}}`,
        ),
      selectedTemplate.body_text,
    );
  }

  async function handleSubmit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    if (!selectedTemplate) {
      onError("Please select a template.");
      return;
    }

    const selectedContacts = contacts.filter(
      (contact) =>
        selectedContactIds.includes(contact.id),
    );

    if (selectedContacts.length === 0) {
      onError(
        "Select at least one contact.",
      );
      return;
    }

    try {
      setSubmitting(true);
      onError(null);

      await createCampaign({
        name: name.trim(),
        template_name: selectedTemplate.name,
        language_code: selectedTemplate.language,
        recipients: selectedContacts.map(
          (contact) => ({
            contact_id: contact.id,
            phone_number: contact.phone_number,
            parameters,
          }),
        ),
        scheduled_at: scheduledAt
          ? new Date(scheduledAt).toISOString()
          : null,
      });

      await onCreated();
    } catch (err) {
      onError(
        err instanceof Error
          ? err.message
          : "Unable to create campaign.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border bg-background p-6 shadow-xl">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">
              Create campaign
            </h2>

            <p className="mt-1 text-sm text-muted-foreground">
              Send an approved WhatsApp template to multiple
              recipients.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-xl text-muted-foreground hover:text-foreground"
          >
            ×
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-6 space-y-5"
        >
          <div>
            <label className="text-sm font-medium">
              Campaign name
            </label>

            <input
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="August promotion"
              required
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="text-sm font-medium">
              WhatsApp template
            </label>

            <select
              value={templateName}
              onChange={(event) =>
                handleTemplateChange(event.target.value)
              }
              required
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
            >
              <option value="">
                Select an approved template
              </option>

              {templates.map((template) => (
                <option
                  key={`${template.name}-${template.language}`}
                  value={template.name}
                >
                  {template.name} — {template.language}
                </option>
              ))}
            </select>
          </div>

          {selectedTemplate &&
            selectedTemplate.placeholder_count > 0 && (
              <div className="space-y-3">
                <label className="text-sm font-medium">
                  Template parameters
                </label>

                {parameters.map((parameter, index) => (
                  <input
                    key={index}
                    value={parameter}
                    onChange={(event) =>
                      updateParameter(
                        index,
                        event.target.value,
                      )
                    }
                    placeholder={`Parameter ${index + 1}`}
                    required
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  />
                ))}
              </div>
            )}

          {selectedTemplate && (
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Message preview
              </div>

              <p className="mt-2 whitespace-pre-wrap text-sm">
                {renderPreview()}
              </p>
            </div>
          )}

          <div>
            <label className="text-sm font-medium">
              Contacts
            </label>

            <p className="mt-1 text-xs text-muted-foreground">
              Select the customers who should receive
              this campaign.
            </p>

            <div className="mt-2 max-h-56 overflow-y-auto rounded-md border">
              {contacts.length === 0 ? (
                <div className="p-4 text-sm text-muted-foreground">
                  No contacts available. Add contacts first.
                </div>
              ) : (
                contacts
                  .filter((contact) => !contact.is_blocked)
                  .map((contact) => (
                    <label
                      key={contact.id}
                      className="flex cursor-pointer items-center gap-3 border-b px-3 py-3 last:border-0 hover:bg-muted/40"
                    >
                      <input
                        type="checkbox"
                        checked={selectedContactIds.includes(
                          contact.id,
                        )}
                        onChange={() =>
                          toggleContact(contact.id)
                        }
                      />

                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium">
                          {contact.name ??
                            contact.profile_name ??
                            "Unnamed contact"}
                        </div>

                        <div className="text-xs text-muted-foreground">
                          {contact.phone_number}
                        </div>
                      </div>
                    </label>
                  ))
              )}
            </div>

            <p className="mt-2 text-xs text-muted-foreground">
              {selectedContactIds.length} contact
              {selectedContactIds.length === 1
                ? ""
                : "s"} selected
            </p>
          </div>

          <div>
            <label className="text-sm font-medium">
              Schedule
            </label>

            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(event) =>
                setScheduledAt(event.target.value)
              }
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
            />

            <p className="mt-1 text-xs text-muted-foreground">
              Leave empty to create the campaign as a draft.
            </p>
          </div>

          <div className="flex justify-end gap-3 border-t pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border px-4 py-2 text-sm font-medium"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {submitting
                ? "Creating..."
                : "Create campaign"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
