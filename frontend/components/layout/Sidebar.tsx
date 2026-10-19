"use client";

import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Bot,
  GitBranch,
  LayoutDashboard,
  Settings,
  ShieldCheck,
} from "lucide-react";

const navigation = [
  {
    name: "Overview",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Incidents",
    href: "/incidents",
    icon: AlertTriangle,
  },
  {
    name: "Investigations",
    href: "/investigations",
    icon: Bot,
  },
  {
    name: "Systems",
    href: "/systems",
    icon: Activity,
  },
  {
    name: "GitHub",
    href: "/github",
    icon: GitBranch,
  },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-zinc-200 bg-white">
      <div className="flex h-16 items-center border-b border-zinc-200 px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-950">
            <ShieldCheck className="h-4 w-4 text-white" />
          </div>

          <div>
            <div className="text-sm font-semibold tracking-tight text-zinc-950">
              DevRescue
            </div>
            <div className="text-[10px] uppercase tracking-widest text-zinc-400">
              AI Reliability
            </div>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
          Workspace
        </div>

        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950"
            >
              <Icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-200 p-4">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-500 hover:bg-zinc-100 hover:text-zinc-950"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
      </div>
    </aside>
  );
}