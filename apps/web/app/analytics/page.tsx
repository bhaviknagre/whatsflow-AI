import { AppShell } from "@/components/layout/app-shell";

export default function Page() {
  return (
    <AppShell>
      <div className="p-6">
        <h1 className="text-2xl font-semibold">
          Analytics
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          Your WhatsApp analytics will appear here.
        </p>
      </div>
    </AppShell>
  );
}
