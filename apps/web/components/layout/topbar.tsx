"use client";

import { Bell, Search } from "lucide-react";

export function Topbar() {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div className="flex w-full max-w-md items-center gap-2 rounded-lg border bg-gray-50 px-3 py-2">
        <Search className="h-4 w-4 text-gray-400" />

        <input
          type="search"
          placeholder="Search conversations, contacts..."
          className="w-full bg-transparent text-sm outline-none placeholder:text-gray-400"
        />
      </div>

      <div className="ml-6 flex items-center gap-4">
        <button
          type="button"
          className="relative rounded-lg p-2 hover:bg-gray-100"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5 text-gray-600" />

          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" />
        </button>

        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-200 text-sm font-semibold">
            B
          </div>

          <div className="hidden sm:block">
            <p className="text-sm font-medium">
              Bhavik
            </p>

            <p className="text-xs text-gray-500">
              Administrator
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}