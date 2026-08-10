import { AppShell } from "@/components/layout/app-shell";

const stats = [
  {
    label: "Open conversations",
    value: "24",
  },
  {
    label: "Unread messages",
    value: "12",
  },
  {
    label: "Contacts",
    value: "1,284",
  },
  {
    label: "Response rate",
    value: "94%",
  },
];

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="space-y-6 p-6">
        <div>
          <h1 className="text-2xl font-semibold">
            Dashboard
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Overview of your WhatsApp business activity.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border bg-white p-5"
            >
              <p className="text-sm text-gray-500">
                {stat.label}
              </p>

              <p className="mt-2 text-3xl font-semibold">
                {stat.value}
              </p>
            </div>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border bg-white p-6">
            <h2 className="font-semibold">
              Recent conversations
            </h2>

            <p className="mt-2 text-sm text-gray-500">
              Your latest WhatsApp conversations will
              appear here.
            </p>
          </section>

          <section className="rounded-xl border bg-white p-6">
            <h2 className="font-semibold">
              WhatsApp connection
            </h2>

            <div className="mt-4 flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-green-500" />

              <div>
                <p className="text-sm font-medium">
                  Connected
                </p>

                <p className="text-xs text-gray-500">
                  WhatsApp Business
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}