"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Inbox,
  LayoutDashboard,
  Megaphone,
  Settings,
  Users,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Inbox",
    href: "/inbox",
    icon: Inbox,
  },
  {
    name: "Contacts",
    href: "/contacts",
    icon: Users,
  },
  {
    name: "Campaigns",
    href: "/campaigns",
    icon: Megaphone,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r bg-white">
      <div className="flex h-16 items-center gap-3 border-b px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-black text-sm font-bold text-white">
          W
        </div>

        <div>
          <p className="font-semibold">WhatsFlow</p>
          <p className="text-xs text-muted-foreground">
            WhatsApp CRM
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active =
            pathname === item.href ||
            pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                active
                  ? "bg-black text-white"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-3">
        <Link
          href="/settings"
          className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
            pathname.startsWith("/settings")
              ? "bg-black text-white"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
      </div>
    </aside>
  );
}