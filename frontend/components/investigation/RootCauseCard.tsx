import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  GitCommit,
} from "lucide-react";

interface RootCauseCardProps {
  confidence?: number;
}

export default function RootCauseCard({
  confidence = 92,
}: RootCauseCardProps) {
  return (
    <section className="overflow-hidden rounded-xl border border-emerald-200 bg-white">
      <div className="flex items-center justify-between border-b border-emerald-100 bg-emerald-50/60 px-6 py-5">
        <div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />

            <h2 className="text-sm font-semibold text-zinc-950">
              Root cause identified
            </h2>
          </div>

          <p className="mt-1 text-xs text-zinc-500">
            DevRescue has enough evidence to propose a remediation.
          </p>
        </div>

        <div className="rounded-md bg-white px-3 py-1.5 text-xs font-semibold text-emerald-700 shadow-sm">
          {confidence}% confidence
        </div>
      </div>

      <div className="p-6">
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </div>

            <div>
              <div className="text-sm font-semibold">
                Database connection pool exhaustion
              </div>

              <p className="mt-2 text-sm leading-6 text-zinc-600">
                A recent payment validation change introduced a database
                connection lifecycle issue. Connections are not being
                released correctly, causing the pool to reach its maximum
                capacity and subsequent payment requests to fail.
              </p>
            </div>
          </div>
        </div>

        {/* Causal chain */}
        <div className="mt-6">
          <div className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
            Causal chain
          </div>

          <div className="flex items-center gap-2">
            <CauseStep
              label="Payment validation"
              description="New DB access"
            />

            <ChevronRight className="h-4 w-4 shrink-0 text-zinc-300" />

            <CauseStep
              label="Connections retained"
              description="Pool grows"
            />

            <ChevronRight className="h-4 w-4 shrink-0 text-zinc-300" />

            <CauseStep
              label="Pool exhausted"
              description="100% utilization"
            />

            <ChevronRight className="h-4 w-4 shrink-0 text-zinc-300" />

            <CauseStep
              label="HTTP 500"
              description="Requests fail"
            />
          </div>
        </div>

        {/* Commit */}
        <div className="mt-6 flex items-center justify-between rounded-lg border border-zinc-200 px-4 py-3">
          <div className="flex items-center gap-3">
            <GitCommit className="h-4 w-4 text-zinc-500" />

            <div>
              <div className="text-xs font-medium">
                Suspected introducing commit
              </div>

              <div className="mt-1 font-mono text-[11px] text-zinc-400">
                7f3a21c · refactor payment validation
              </div>
            </div>
          </div>

          <span className="rounded-md bg-red-50 px-2 py-1 text-[10px] font-medium text-red-700">
            Likely regression
          </span>
        </div>
      </div>
    </section>
  );
}

function CauseStep({
  label,
  description,
}: {
  label: string;
  description: string;
}) {
  return (
    <div className="min-w-0 flex-1 rounded-lg border border-zinc-200 bg-white p-3">
      <div className="truncate text-xs font-medium">
        {label}
      </div>

      <div className="mt-1 text-[10px] text-zinc-400">
        {description}
      </div>
    </div>
  );
}