import { Bell, CircleCheck } from "lucide-react";

export default function Topbar() {
  return (
    <header className="fixed left-64 right-0 top-0 z-30 flex h-16 items-center justify-between border-b border-zinc-200 bg-white/95 px-8 backdrop-blur">
      <div>
        <div className="text-sm font-medium text-zinc-900">
          Reliability Command Center
        </div>
        <div className="text-xs text-zinc-400">
          Autonomous investigation with human-controlled remediation
        </div>
      </div>

      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <CircleCheck className="h-4 w-4 text-emerald-500" />
          All systems operational
        </div>

        <button className="relative rounded-lg p-2 text-zinc-500 hover:bg-zinc-100">
          <Bell className="h-4 w-4" />
          <span className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-red-500" />
        </button>
      </div>
    </header>
  );
}