import Link from "next/link";
import {
  AlertCircle,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  Clock3,
  GitPullRequest,
  ShieldCheck,
} from "lucide-react";

const stats = [
  {
    label: "Active incidents",
    value: "3",
    icon: AlertCircle,
  },
  {
    label: "Investigations",
    value: "2",
    icon: Bot,
  },
  {
    label: "Resolved",
    value: "47",
    icon: CheckCircle2,
  },
  {
    label: "PRs created",
    value: "12",
    icon: GitPullRequest,
  },
];

const incidents = [
  {
    id: "INC-1042",
    service: "payment-service",
    title: "Payment validation failures",
    severity: "Critical",
    status: "Investigating",
    confidence: "92%",
    time: "4 min ago",
  },
  {
    id: "INC-1041",
    service: "orders-api",
    title: "Database connection failures",
    severity: "High",
    status: "Root cause found",
    confidence: "94%",
    time: "18 min ago",
  },
  {
    id: "INC-1040",
    service: "notification-service",
    title: "Delivery latency increased",
    severity: "Medium",
    status: "Investigating",
    confidence: "71%",
    time: "32 min ago",
  },
];

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="flex items-end justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-zinc-400">
            <ShieldCheck className="h-3.5 w-3.5" />
            DevRescue
          </div>

          <h1 className="text-3xl font-semibold tracking-tight">
            Reliability overview
          </h1>

          <p className="mt-2 text-sm text-zinc-500">
            Investigate failures, understand root causes, and safely
            remediate them.
          </p>
        </div>

        <Link
          href="/investigations/new"
          className="flex items-center gap-2 rounded-lg bg-zinc-950 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800"
        >
          <Bot className="h-4 w-4" />
          New investigation
        </Link>
      </section>

      {/* Stats */}
      <section className="grid grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;

          return (
            <div
              key={stat.label}
              className="rounded-xl border border-zinc-200 bg-white p-5"
            >
              <div className="flex items-center justify-between">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100">
                  <Icon className="h-4 w-4 text-zinc-700" />
                </div>

                <ArrowUpRight className="h-4 w-4 text-zinc-300" />
              </div>

              <div className="mt-5 text-2xl font-semibold">
                {stat.value}
              </div>

              <div className="mt-1 text-xs text-zinc-500">
                {stat.label}
              </div>
            </div>
          );
        })}
      </section>

      {/* Active incidents */}
      <section className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-5">
          <div>
            <h2 className="text-sm font-semibold">
              Active incidents
            </h2>

            <p className="mt-1 text-xs text-zinc-400">
              Failures currently being investigated by DevRescue
            </p>
          </div>

          <Link
            href="/incidents"
            className="text-xs font-medium text-zinc-500 hover:text-zinc-950"
          >
            View all
          </Link>
        </div>

        <div>
          {incidents.map((incident) => (
            <Link
              key={incident.id}
              href={`/investigations/${incident.id}`}
              className="flex items-center justify-between border-b border-zinc-100 px-6 py-5 transition hover:bg-zinc-50 last:border-b-0"
            >
              <div className="flex items-center gap-4">
                <div
                  className={`h-2.5 w-2.5 rounded-full ${
                    incident.severity === "Critical"
                      ? "bg-red-500"
                      : incident.severity === "High"
                        ? "bg-orange-500"
                        : "bg-yellow-500"
                  }`}
                />

                <div>
                  <div className="text-sm font-medium">
                    {incident.title}
                  </div>

                  <div className="mt-1 text-xs text-zinc-400">
                    {incident.service} · {incident.time}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-8">
                <div className="text-right">
                  <div className="text-xs font-medium">
                    {incident.status}
                  </div>

                  <div className="mt-1 text-xs text-zinc-400">
                    Confidence {incident.confidence}
                  </div>
                </div>

                <Clock3 className="h-4 w-4 text-zinc-300" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}