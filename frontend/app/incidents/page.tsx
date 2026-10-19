import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CheckCircle2,
  Clock3,
  Database,
  GitBranch,
  Loader2,
  Search,
  ShieldCheck,
  Terminal,
  Wrench,
  XCircle,
} from "lucide-react";

const timeline = [
  {
    title: "Incident received",
    description: "Failure context accepted",
    status: "complete",
    time: "10:42:01",
  },
  {
    title: "Repository inspected",
    description: "Recent commits and changes analyzed",
    status: "complete",
    time: "10:42:08",
  },
  {
    title: "Observability queried",
    description: "Logs and metrics correlated",
    status: "complete",
    time: "10:42:19",
  },
  {
    title: "Database inspected",
    description: "Connection health being analyzed",
    status: "active",
    time: "10:42:27",
  },
  {
    title: "Root cause analysis",
    description: "Waiting for evidence correlation",
    status: "pending",
    time: "",
  },
];

const evidence = [
  {
    source: "GitHub",
    type: "Recent commit",
    title: "Refactor payment validation",
    description:
      "payment/validator.py modified validation and database access logic.",
    icon: GitBranch,
    status: "Supporting",
  },
  {
    source: "Observability",
    type: "Application logs",
    title: "Database connection refused",
    description:
      "Error frequency increased immediately after deployment.",
    icon: Terminal,
    status: "Supporting",
  },
  {
    source: "Database",
    type: "Connection metrics",
    title: "Pool utilization at 100%",
    description:
      "Connection pool reached its configured maximum.",
    icon: Database,
    status: "Supporting",
  },
  {
    source: "GitHub",
    type: "Deployment history",
    title: "Deployment completed 6 min ago",
    description:
      "Failure began shortly after version 4.8.2 was deployed.",
    icon: GitBranch,
    status: "Supporting",
  },
];

const activity = [
  {
    tool: "GitHub MCP",
    action: "Inspected recent commits",
    time: "10:42:08",
  },
  {
    tool: "Observability MCP",
    action: "Queried payment-service logs",
    time: "10:42:19",
  },
  {
    tool: "Database MCP",
    action: "Checked connection pool",
    time: "10:42:27",
  },
];

interface InvestigationPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function InvestigationPage({
  params,
}: InvestigationPageProps) {
  const { id } = await params;

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="rounded-xl border border-zinc-200 bg-white">
        <div className="flex items-start justify-between border-b border-zinc-200 px-6 py-5">
          <div>
            <Link
              href="/incidents"
              className="mb-4 inline-flex items-center gap-2 text-xs text-zinc-400 hover:text-zinc-950"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Incidents
            </Link>

            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight">
                    Payment validation failures
                  </h1>

                  <span className="rounded-md bg-red-50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-red-700">
                    Critical
                  </span>
                </div>

                <div className="mt-1 flex items-center gap-2 text-xs text-zinc-400">
                  <span>payment-service</span>
                  <span>·</span>
                  <span>production</span>
                  <span>·</span>
                  <span className="font-mono">{id}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-5">
            <div className="text-right">
              <div className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
                Investigation confidence
              </div>

              <div className="mt-1 text-2xl font-semibold">
                92%
              </div>
            </div>

            <div className="h-10 w-px bg-zinc-200" />

            <div className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-xs font-medium text-blue-700">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Investigating
            </div>
          </div>
        </div>

        {/* Progress */}
        <div className="px-6 py-4">
          <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-zinc-400">
            <span>Investigation progress</span>
            <span>4 / 5 stages</span>
          </div>

          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-zinc-100">
            <div className="h-full w-4/5 rounded-full bg-zinc-900" />
          </div>
        </div>
      </section>

      {/* Workspace */}
      <div className="grid grid-cols-[360px_1fr] gap-6">
        {/* Left column */}
        <div className="space-y-6">
          {/* Timeline */}
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-5 py-4">
              <h2 className="text-sm font-semibold">
                Investigation timeline
              </h2>
            </div>

            <div className="p-5">
              {timeline.map((item, index) => (
                <div
                  key={item.title}
                  className="relative flex gap-4"
                >
                  {index !== timeline.length - 1 && (
                    <div className="absolute left-[11px] top-6 h-[calc(100%-2px)] w-px bg-zinc-200" />
                  )}

                  <TimelineIcon status={item.status} />

                  <div className="pb-6">
                    <div className="text-sm font-medium">
                      {item.title}
                    </div>

                    <div className="mt-1 text-xs leading-5 text-zinc-400">
                      {item.description}
                    </div>

                    {item.time && (
                      <div className="mt-2 flex items-center gap-1.5 text-[10px] text-zinc-400">
                        <Clock3 className="h-3 w-3" />
                        {item.time}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Agent activity */}
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4">
              <div>
                <h2 className="text-sm font-semibold">
                  Agent activity
                </h2>

                <p className="mt-1 text-[11px] text-zinc-400">
                  Tools used during investigation
                </p>
              </div>

              <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            </div>

            <div className="divide-y divide-zinc-100">
              {activity.map((item) => (
                <div key={item.tool} className="px-5 py-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">
                      {item.tool}
                    </span>

                    <span className="text-[10px] text-zinc-400">
                      {item.time}
                    </span>
                  </div>

                  <div className="mt-1 text-xs text-zinc-500">
                    {item.action}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Current hypothesis */}
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-5">
              <div>
                <div className="mb-1 flex items-center gap-2">
                  <Search className="h-4 w-4 text-zinc-500" />

                  <h2 className="text-sm font-semibold">
                    Current hypothesis
                  </h2>
                </div>

                <p className="text-xs text-zinc-400">
                  Evidence-backed explanation currently being evaluated
                </p>
              </div>

              <span className="rounded-md bg-purple-50 px-2 py-1 text-[10px] font-semibold text-purple-700">
                92% confidence
              </span>
            </div>

            <div className="p-6">
              <div className="rounded-lg border border-purple-100 bg-purple-50/50 p-5">
                <div className="text-sm font-semibold text-zinc-900">
                  Database connection pool exhaustion
                </div>

                <p className="mt-2 text-sm leading-6 text-zinc-600">
                  The latest payment validation change appears to create
                  additional database connections without releasing them
                  correctly. The resulting pool exhaustion is causing
                  subsequent payment requests to fail.
                </p>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-4">
                <Signal
                  type="supporting"
                  title="Pool utilization"
                  value="100%"
                />

                <Signal
                  type="supporting"
                  title="Error correlation"
                  value="Strong"
                />

                <Signal
                  type="supporting"
                  title="Deployment timing"
                  value="6 min"
                />

                <Signal
                  type="contradicting"
                  title="Other services"
                  value="Healthy"
                />
              </div>
            </div>
          </section>

          {/* Evidence */}
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-5">
              <div>
                <h2 className="text-sm font-semibold">
                  Evidence collected
                </h2>

                <p className="mt-1 text-xs text-zinc-400">
                  Signals DevRescue used to evaluate the hypothesis
                </p>
              </div>

              <span className="text-xs text-zinc-400">
                {evidence.length} signals
              </span>
            </div>

            <div className="divide-y divide-zinc-100">
              {evidence.map((item) => {
                const Icon = item.icon;

                return (
                  <div
                    key={item.title}
                    className="flex items-start gap-4 px-6 py-5"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-100">
                      <Icon className="h-4 w-4 text-zinc-600" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                          {item.source}
                        </span>

                        <span className="text-[10px] text-zinc-300">
                          /
                        </span>

                        <span className="text-[10px] text-zinc-400">
                          {item.type}
                        </span>
                      </div>

                      <div className="mt-1 text-sm font-medium">
                        {item.title}
                      </div>

                      <div className="mt-1 text-xs leading-5 text-zinc-500">
                        {item.description}
                      </div>
                    </div>

                    <span className="rounded-md bg-emerald-50 px-2 py-1 text-[10px] font-medium text-emerald-700">
                      {item.status}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Investigation status */}
          <section className="rounded-xl border border-zinc-200 bg-zinc-950 p-6 text-white">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Wrench className="h-4 w-4" />

                  <h2 className="text-sm font-semibold">
                    Investigation in progress
                  </h2>
                </div>

                <p className="mt-2 max-w-xl text-xs leading-5 text-zinc-400">
                  DevRescue is correlating the database evidence with the
                  recent payment-service code changes before generating a
                  remediation proposal.
                </p>
              </div>

              <div className="rounded-lg border border-zinc-700 px-3 py-2 text-[10px] text-zinc-400">
                No writes performed
              </div>
            </div>

            <div className="mt-5 flex items-center gap-2 text-xs text-zinc-400">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              Human approval required before remediation
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function TimelineIcon({
  status,
}: {
  status: string;
}) {
  if (status === "complete") {
    return (
      <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100">
        <Check className="h-3.5 w-3.5 text-emerald-600" />
      </div>
    );
  }

  if (status === "active") {
    return (
      <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100">
        <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-zinc-200 bg-white">
      <div className="h-2 w-2 rounded-full bg-zinc-300" />
    </div>
  );
}

function Signal({
  type,
  title,
  value,
}: {
  type: "supporting" | "contradicting";
  title: string;
  value: string;
}) {
  const supporting = type === "supporting";

  return (
    <div className="rounded-lg border border-zinc-200 p-4">
      <div className="flex items-center gap-2">
        {supporting ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
        ) : (
          <XCircle className="h-3.5 w-3.5 text-orange-500" />
        )}

        <span className="text-[10px] uppercase tracking-wider text-zinc-400">
          {supporting ? "Supporting" : "Contradicting"}
        </span>
      </div>

      <div className="mt-3 text-xs text-zinc-500">
        {title}
      </div>

      <div className="mt-1 text-sm font-semibold">
        {value}
      </div>
    </div>
  );
}