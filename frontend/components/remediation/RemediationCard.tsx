import {
  CheckCircle2,
  FileCode2,
  ShieldCheck,
  Wrench,
} from "lucide-react";

export default function RemediationCard() {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white">
      <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-5">
        <div>
          <div className="flex items-center gap-2">
            <Wrench className="h-4 w-4 text-zinc-600" />

            <h2 className="text-sm font-semibold">
              Proposed remediation
            </h2>
          </div>

          <p className="mt-1 text-xs text-zinc-400">
            A minimal change designed to address the identified root cause.
          </p>
        </div>

        <span className="rounded-md bg-blue-50 px-2 py-1 text-[10px] font-medium text-blue-700">
          Proposal
        </span>
      </div>

      <div className="p-6">
        {/* Proposal */}
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white">
              <FileCode2 className="h-4 w-4 text-zinc-600" />
            </div>

            <div>
              <div className="text-sm font-semibold">
                Correct database connection lifecycle
              </div>

              <p className="mt-2 text-xs leading-5 text-zinc-500">
                Ensure database connections are released after payment
                validation completes, including when validation raises an
                exception.
              </p>
            </div>
          </div>
        </div>

        {/* Changes */}
        <div className="mt-5">
          <div className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
            Proposed changes
          </div>

          <div className="space-y-2">
            <Change
              file="payment/validator.py"
              description="Wrap database access in managed connection lifecycle"
            />

            <Change
              file="payment/service.py"
              description="Remove duplicate connection acquisition"
            />

            <Change
              file="tests/test_validator.py"
              description="Add regression test for connection release"
            />
          </div>
        </div>

        {/* Safety */}
        <div className="mt-5 flex items-start gap-3 rounded-lg border border-emerald-100 bg-emerald-50 p-4">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />

          <div>
            <div className="text-xs font-medium text-emerald-900">
              Low-risk remediation
            </div>

            <p className="mt-1 text-[11px] leading-5 text-emerald-700">
              The proposed patch is limited to connection lifecycle handling
              and a regression test. No infrastructure or database schema
              changes are proposed.
            </p>
          </div>
        </div>

        {/* Status */}
        <div className="mt-5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            Evidence supports this remediation
          </div>

          <button className="flex items-center gap-2 rounded-lg bg-zinc-950 px-4 py-2.5 text-xs font-medium text-white transition hover:bg-zinc-800">
            Review patch
          </button>
        </div>
      </div>
    </section>
  );
}

function Change({
  file,
  description,
}: {
  file: string;
  description: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3">
      <div>
        <div className="font-mono text-xs font-medium text-zinc-800">
          {file}
        </div>

        <div className="mt-1 text-[11px] text-zinc-400">
          {description}
        </div>
      </div>

      <span className="rounded-md bg-zinc-100 px-2 py-1 text-[10px] text-zinc-500">
        Modified
      </span>
    </div>
  );
}