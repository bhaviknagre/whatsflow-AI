export const metadata = {
  title: "Privacy Policy — WhatsFlow AI",
};

export default function PrivacyPolicyPage() {
  return (
    <main className="mx-auto max-w-3xl space-y-8 p-6 py-16">
      <div>
        <h1 className="text-3xl font-bold">Privacy Policy</h1>
        <p className="mt-2 text-muted-foreground">
          Last updated: August 8, 2026
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Overview</h2>
        <p>
          WhatsFlow AI (&quot;we&quot;, &quot;us&quot;) provides a WhatsApp-based
          customer relationship management platform for businesses. This
          policy explains what information we collect, how we use it, and
          the choices you have.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Information We Collect</h2>
        <ul className="list-disc space-y-2 pl-6">
          <li>
            <strong>Account information:</strong> name, email address, and
            hashed password when you register an organization.
          </li>
          <li>
            <strong>WhatsApp Business data:</strong> when you connect a
            WhatsApp Business Account via Meta, we store your WABA ID, phone
            number ID, display name, and an encrypted access token needed to
            send and receive messages on your behalf.
          </li>
          <li>
            <strong>Conversation data:</strong> messages and metadata
            exchanged between your business and your customers through the
            WhatsApp Business Platform, so they can be displayed in your
            inbox.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">How We Use Information</h2>
        <p>
          We use the information above solely to operate the service:
          authenticating your account, sending and receiving WhatsApp
          messages on your behalf, and displaying your conversations. We do
          not sell your data or your customers&apos; data to third parties.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Data Sharing</h2>
        <p>
          We share data with Meta Platforms, Inc. only as required to
          deliver WhatsApp messages through the WhatsApp Business Platform.
          We do not share your data with any other third party except where
          required by law.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Data Retention &amp; Security</h2>
        <p>
          Access tokens are stored encrypted at rest. You may request
          deletion of your organization&apos;s account and associated data
          at any time by contacting us using the details below.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Contact</h2>
        <p>
          Questions about this policy can be sent to{" "}
          <a
            href="mailto:privacy@whatsflow.example.com"
            className="underline"
          >
            privacy@whatsflow.example.com
          </a>
          .
        </p>
      </section>
    </main>
  );
}
