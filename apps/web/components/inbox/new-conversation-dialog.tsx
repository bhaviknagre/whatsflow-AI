"use client";

import { Dialog } from "@base-ui/react/dialog";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  getMessageTemplates,
  startConversation,
} from "@/lib/inbox/api";
import type {
  ConversationResponse,
  MessageTemplateSummary,
} from "@/lib/inbox/types";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConversationStarted: (
    conversation: ConversationResponse,
  ) => void;
};

function renderPreview(
  bodyText: string | null,
  parameterValues: string[],
): string {
  if (!bodyText) {
    return "";
  }

  return parameterValues.reduce(
    (text, value, index) =>
      text.replaceAll(
        `{{${index + 1}}}`,
        value || `{{${index + 1}}}`,
      ),
    bodyText,
  );
}

export function NewConversationDialog({
  open,
  onOpenChange,
  onConversationStarted,
}: Props) {
  return (
    <Dialog.Root
      open={open}
      onOpenChange={onOpenChange}
    >
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/50" />

        <Dialog.Popup className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-background p-6 shadow-lg">
          <Dialog.Title className="text-lg font-semibold">
            New conversation
          </Dialog.Title>

          {open && (
            <NewConversationForm
              key={
                open ? "open" : "closed"
              }
              onClose={() =>
                onOpenChange(false)
              }
              onConversationStarted={
                onConversationStarted
              }
            />
          )}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function NewConversationForm({
  onClose,
  onConversationStarted,
}: {
  onClose: () => void;
  onConversationStarted: (
    conversation: ConversationResponse,
  ) => void;
}) {
  const [templates, setTemplates] = useState<
    MessageTemplateSummary[]
  >([]);

  const [templatesLoading, setTemplatesLoading] =
    useState(true);

  const [templatesError, setTemplatesError] =
    useState<string | null>(null);

  const [phoneNumber, setPhoneNumber] = useState("");

  const [selectedTemplateName, setSelectedTemplateName] =
    useState("");

  const [parameterValues, setParameterValues] = useState<
    string[]
  >([]);

  const [submitting, setSubmitting] = useState(false);

  const [submitError, setSubmitError] = useState<
    string | null
  >(null);

  useEffect(() => {
    async function loadTemplates() {
      try {
        const data = await getMessageTemplates();

        setTemplates(data);
      } catch (err) {
        setTemplatesError(
          err instanceof Error
            ? err.message
            : "Unable to load templates.",
        );
      } finally {
        setTemplatesLoading(false);
      }
    }

    void loadTemplates();
  }, []);

  const selectedTemplate = templates.find(
    (template) =>
      template.name === selectedTemplateName,
  );

  function handleTemplateChange(name: string) {
    setSelectedTemplateName(name);

    const template = templates.find(
      (item) => item.name === name,
    );

    setParameterValues(
      Array(template?.placeholder_count ?? 0).fill(
        "",
      ),
    );
  }

  function handleParameterChange(
    index: number,
    value: string,
  ) {
    setParameterValues((current) =>
      current.map((existing, i) =>
        i === index ? value : existing,
      ),
    );
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (!selectedTemplate || !phoneNumber.trim()) {
      return;
    }

    try {
      setSubmitting(true);
      setSubmitError(null);

      const conversation = await startConversation({
        customer_phone_number: phoneNumber.trim(),
        template_name: selectedTemplate.name,
        language_code: selectedTemplate.language,
        parameters: parameterValues,
      });

      onConversationStarted(conversation);
      onClose();
    } catch (err) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : "Unable to start conversation.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-4 space-y-4"
    >
      <div>
        <label className="text-sm font-medium">
          Phone number
        </label>

        <input
          value={phoneNumber}
          onChange={(event) =>
            setPhoneNumber(event.target.value)
          }
          placeholder="919876543210"
          required
          className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      {templatesLoading && (
        <p className="text-sm text-muted-foreground">
          Loading templates...
        </p>
      )}

      {templatesError && (
        <p className="text-sm text-destructive">
          {templatesError}
        </p>
      )}

      {!templatesLoading &&
        !templatesError &&
        templates.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No approved templates yet. Create and
            get one approved in WhatsApp Manager
            first.
          </p>
        )}

      {templates.length > 0 && (
        <div>
          <label className="text-sm font-medium">
            Template
          </label>

          <select
            value={selectedTemplateName}
            onChange={(event) =>
              handleTemplateChange(
                event.target.value,
              )
            }
            required
            className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="">
              Select a template
            </option>

            {templates.map((template) => (
              <option
                key={template.name}
                value={template.name}
              >
                {template.name} (
                {template.language})
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedTemplate &&
        parameterValues.map((value, index) => (
          <div key={index}>
            <label className="text-sm font-medium">
              Variable {index + 1}
            </label>

            <input
              value={value}
              onChange={(event) =>
                handleParameterChange(
                  index,
                  event.target.value,
                )
              }
              required
              className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
        ))}

      {selectedTemplate && (
        <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
          {renderPreview(
            selectedTemplate.body_text,
            parameterValues,
          )}
        </div>
      )}

      {submitError && (
        <p className="text-sm text-destructive">
          {submitError}
        </p>
      )}

      <div className="flex justify-end gap-2">
        <Dialog.Close
          render={
            <Button
              type="button"
              variant="outline"
            />
          }
        >
          Cancel
        </Dialog.Close>

        <Button
          type="submit"
          disabled={
            submitting ||
            !selectedTemplate ||
            !phoneNumber.trim()
          }
        >
          {submitting
            ? "Sending..."
            : "Start conversation"}
        </Button>
      </div>
    </form>
  );
}
