import { MetaEmbeddedSignup } from "@/components/meta/meta-embedded-signup";
import { MetaSDK } from "@/components/meta/meta-sdk";

export default function WhatsAppSettingsPage() {
  return (
    <main className="min-h-screen bg-gray-50 px-6 py-12">
      <div className="mx-auto max-w-3xl">
        <div className="rounded-2xl border bg-white p-8 shadow-sm">
          <div className="mb-8">
            <p className="text-sm font-medium text-green-600">
              WhatsFlow AI
            </p>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Connect WhatsApp
            </h1>

            <p className="mt-3 text-gray-600">
              Connect your WhatsApp Business account to manage
              conversations, contacts and customer communication
              from WhatsFlow.
            </p>
          </div>

          <div className="rounded-xl border bg-gray-50 p-6">
            <h2 className="text-lg font-semibold">
              WhatsApp Business
            </h2>

            <p className="mt-2 text-sm text-gray-600">
              Connect your existing WhatsApp Business setup using
              Meta&apos;s official onboarding flow.
            </p>

            <div className="mt-6">
              <MetaSDK />
              <MetaEmbeddedSignup />
            </div>
          </div>

          <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="text-sm text-blue-800">
              Your WhatsApp credentials are securely handled by
              WhatsFlow. We do not ask you to provide your WhatsApp
              password.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}