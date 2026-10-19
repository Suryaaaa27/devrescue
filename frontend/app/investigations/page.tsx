import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock3,
  Filter,
  Search,
  ShieldCheck,
} from "lucide-react";

const investigations = [
  {
    id: "INV-1042",
    incident: "Payment validation failures",
    service: "payment-service",
    environment: "production",
    status: "Investigating",
    severity: "Critical",
    confidence: "92%",
    started: "4 min ago",
    stage: "Evidence correlation",
  },
  {
    id: "INV-1041",
    incident: "Database connection failures",
    service: "orders-api",
    environment: "production",
    status: "Root cause identified",
    severity: "High",
    confidence: "94%",
    started: "18 min ago",
    stage: "Root cause",
  },
  {
    id: "INV-1040",
    incident: "Delivery latency increased",
    service: "notification-service",
    environment: "production",
    status: "Investigating",
    severity: "Medium",
    confidence: "71%",
    started: "32 min ago",
    stage: "Hypothesis evaluation",
  },
  {
    id: "INV-1039",
    incident: "Authentication latency spike",
    service: "user-service",
    environment: "production",
    status: "Resolved",
    severity: "Medium",
    confidence: "97%",
    started: "1 hr ago",
    stage: "Completed",
  },
  {
    id: "INV-1038",
    incident: "Inventory synchronization delay",
    service: "inventory-service",
    environment: "staging",
    status: "Resolved",
    severity: "Low",
    confidence: "95%",
    started: "2 hrs ago",
    stage: "Completed",
  },
];

function severityStyles(severity: string) {
  switch (severity) {
    case "Critical":
      return "border-red-200 bg-red-50 text-red-700";

    case "High":
      return "border-orange-200 bg-orange-50 text-orange-700";

    case "Medium":
      return "border-yellow-200 bg-yellow-50 text-yellow-700";

    default:
      return "border-zinc-200 bg-zinc-50 text-zinc-600";
  }
}

function statusStyles(status: string) {
  switch (status) {
    case "Investigating":
      return "bg-blue-50 text-blue-700";

    case "Root cause identified":
      return "bg-purple-50 text-purple-700";

    case "Resolved":
      return "bg-emerald-50 text-emerald-700";

    default:
      return "bg-zinc-50 text-zinc-600";
  }
}

function statusIcon(status: string) {
  if (status === "Resolved") {
    return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />;
  }

  if (status === "Root cause identified") {
    return <ShieldCheck className="h-3.5 w-3.5 text-purple-500" />;
  }

  return <Bot className="h-3.5 w-3.5 text-blue-500" />;
}

export default function InvestigationsPage() {
  return (
    <div className="space-y-7">
      {/* =========================================================
          HEADER
      ========================================================= */}
      <section className="flex items-end justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-zinc-400">
            <Bot className="h-3.5 w-3.5" />
            AI Reliability
          </div>

          <h1 className="text-3xl font-semibold tracking-tight">
            Investigations
          </h1>

          <p className="mt-2 text-sm text-zinc-500">
            Track investigations, evidence collection, hypotheses and
            root-cause analysis.
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

      {/* =========================================================
          SUMMARY
      ========================================================= */}
      <section className="grid grid-cols-4 gap-4">
        <SummaryCard
          icon={Bot}
          value="2"
          label="Active investigations"
          iconClass="bg-blue-50 text-blue-600"
        />

        <SummaryCard
          icon={AlertCircle}
          value="1"
          label="Root cause identified"
          iconClass="bg-purple-50 text-purple-600"
        />

        <SummaryCard
          icon={Clock3}
          value="6.4 min"
          label="Avg. investigation time"
          iconClass="bg-zinc-100 text-zinc-600"
        />

        <SummaryCard
          icon={CheckCircle2}
          value="47"
          label="Successfully resolved"
          iconClass="bg-emerald-50 text-emerald-600"
        />
      </section>

      {/* =========================================================
          FILTERS
      ========================================================= */}
      <section className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2">
            <Search className="h-4 w-4 text-zinc-400" />

            <input
              type="text"
              placeholder="Search investigations..."
              className="w-64 bg-transparent text-sm outline-none placeholder:text-zinc-400"
            />
          </div>

          <button className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-600 transition hover:bg-zinc-50">
            <Filter className="h-4 w-4" />
            Filters
          </button>
        </div>

        <div className="text-xs text-zinc-400">
          {investigations.length} investigations
        </div>
      </section>

      {/* =========================================================
          INVESTIGATION TABLE
      ========================================================= */}
      <section className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
        {/* Table header */}
        <div className="grid grid-cols-[1fr_150px_150px_120px_40px] gap-4 border-b border-zinc-200 bg-zinc-50/70 px-6 py-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
          <div>Investigation</div>
          <div>Status</div>
          <div>Severity</div>
          <div>Started</div>
          <div />
        </div>

        {/* Rows */}
        {investigations.map((investigation) => (
          <Link
            key={investigation.id}
            href={`/investigations/${investigation.id}`}
            className="grid grid-cols-[1fr_150px_150px_120px_40px] items-center gap-4 border-b border-zinc-100 px-6 py-5 transition last:border-b-0 hover:bg-zinc-50"
          >
            {/* Investigation */}
            <div className="flex items-start gap-4">
              <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-100">
                {statusIcon(investigation.status)}
              </div>

              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-zinc-950">
                    {investigation.incident}
                  </span>

                  <span className="font-mono text-[10px] text-zinc-400">
                    {investigation.id}
                  </span>
                </div>

                <div className="mt-1 text-xs text-zinc-400">
                  {investigation.service} · {investigation.environment}
                </div>

                <div className="mt-2 flex items-center gap-3">
                  <span className="text-[11px] text-zinc-500">
                    Stage: {investigation.stage}
                  </span>

                  <span className="text-[11px] text-zinc-300">
                    ·
                  </span>

                  <span className="text-[11px] text-zinc-500">
                    Confidence {investigation.confidence}
                  </span>
                </div>
              </div>
            </div>

            {/* Status */}
            <div>
              <span
                className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-medium ${statusStyles(
                  investigation.status
                )}`}
              >
                {investigation.status}
              </span>
            </div>

            {/* Severity */}
            <div>
              <span
                className={`inline-flex rounded-md border px-2 py-1 text-[11px] font-medium ${severityStyles(
                  investigation.severity
                )}`}
              >
                {investigation.severity}
              </span>
            </div>

            {/* Started */}
            <div className="flex items-center gap-1.5 text-xs text-zinc-400">
              <Clock3 className="h-3.5 w-3.5" />

              {investigation.started}
            </div>

            <ArrowRight className="h-4 w-4 text-zinc-300" />
          </Link>
        ))}
      </section>

      {/* =========================================================
          PRODUCT PRINCIPLE
      ========================================================= */}
      <section className="rounded-xl border border-zinc-200 bg-zinc-950 p-6 text-white">
        <div className="flex items-start gap-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/10">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>

          <div>
            <div className="text-sm font-semibold">
              Human-controlled remediation
            </div>

            <p className="mt-1 max-w-3xl text-xs leading-5 text-zinc-400">
              DevRescue can investigate failures, correlate evidence, identify
              probable root causes and prepare remediation proposals. No
              production change or GitHub write is performed without explicit
              human approval.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function SummaryCard({
  icon: Icon,
  value,
  label,
  iconClass,
}: {
  icon: typeof Bot;
  value: string;
  label: string;
  iconClass: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <div
        className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconClass}`}
      >
        <Icon className="h-4 w-4" />
      </div>

      <div className="mt-5 text-2xl font-semibold">
        {value}
      </div>

      <div className="mt-1 text-xs text-zinc-500">
        {label}
      </div>
    </div>
  );
}