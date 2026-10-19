
"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Bot,
  CheckCircle2,
  Database,
  GitBranch,
  Loader2,
  Search,
  ShieldCheck,
  Terminal,
} from "lucide-react";

import { getInvestigation } from "@/lib/api";
import type { InvestigationDetail } from "@/types/investigation";

interface InvestigationWorkspaceClientProps {
  id: string;
}

export default function InvestigationWorkspaceClient({
  id,
}: InvestigationWorkspaceClientProps) {
  const [investigation, setInvestigation] =
    useState<InvestigationDetail | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadInvestigation() {
      setLoading(true);
      setError("");
      setInvestigation(null);

      try {
        console.log("Loading investigation ID:", id);

        const result = await getInvestigation(id);

        if (!cancelled) {
          setInvestigation(result);
        }
      } catch (err) {
        console.error("Failed to load investigation:", err);

        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load investigation."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    if (id) {
      void loadInvestigation();
    } else {
      setError("No investigation ID was provided.");
      setLoading(false);
    }

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="flex items-center gap-3 text-sm text-zinc-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading investigation...
        </div>
      </div>
    );
  }

  if (error || !investigation) {
    return (
      <div className="mx-auto max-w-3xl py-20">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />

            <div>
              <h1 className="text-sm font-semibold text-red-900">
                Investigation unavailable
              </h1>

              <p className="mt-1 text-xs leading-5 text-red-700">
                {error || "Investigation not found."}
              </p>

              <p className="mt-2 text-xs leading-5 text-red-700">
                Check that the investigation exists in the backend and
                that the URL contains its correct ID.
              </p>

              <a
                href="/investigations"
                className="mt-4 inline-flex items-center gap-2 text-xs font-medium text-red-900 underline underline-offset-4"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back to investigations
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const confidence = Math.round(
    (investigation.confidence ?? 0) * 100
  );

  const activityItems = investigation.activity ?? [];
  const evidenceItems = investigation.evidence ?? [];
  const hypotheses = investigation.hypotheses ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <div className="mb-3 flex flex-wrap items-center gap-3 text-xs text-zinc-400">
            <a
              href="/investigations"
              className="flex items-center gap-1.5 transition hover:text-zinc-900"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Investigations
            </a>

            <span>/</span>

            <span className="font-mono">{investigation.id}</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-zinc-950">
              <Bot className="h-5 w-5 text-white" />
            </div>

            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                Investigation workspace
              </h1>

              <p className="mt-1 text-sm text-zinc-500">
                {investigation.service} · {investigation.environment}
              </p>
            </div>
          </div>
        </div>

        <StatusBadge status={investigation.status} />
      </header>

      {/* Investigation metrics */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="Investigation"
          value={investigation.id}
          mono
        />

        <Metric
          label="Current stage"
          value={investigation.currentStage || "Created"}
        />

        <Metric
          label="Confidence"
          value={
            confidence > 0
              ? `${confidence}%`
              : "Building evidence"
          }
        />

        <Metric
          label="Environment"
          value={investigation.environment}
        />
      </section>

      {/* Main workspace */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <main className="min-w-0 space-y-6">
          {/* Agent activity */}
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="flex items-center justify-between gap-3 border-b border-zinc-200 px-5 py-5 sm:px-6">
              <div>
                <h2 className="text-sm font-semibold">
                  Investigation activity
                </h2>

                <p className="mt-1 text-xs text-zinc-400">
                  Evidence collection and reasoning state
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <Activity className="h-3.5 w-3.5" />
                Activity
              </div>
            </div>

            <div className="p-5 sm:p-6">
              {activityItems.length === 0 ? (
                <EmptyState
                  icon={<Search className="h-5 w-5" />}
                  title="Investigation started"
                  description="DevRescue is ready to collect evidence from connected systems. Activity will appear here when the backend records it."
                />
              ) : (
                <div className="space-y-5">
                  {activityItems.map((item) => (
                    <ActivityItem
                      key={item.id}
                      tool={item.tool}
                      action={item.action}
                      status={item.status}
                      timestamp={item.timestamp}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Evidence */}
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-5 py-5 sm:px-6">
              <h2 className="text-sm font-semibold">Evidence</h2>

              <p className="mt-1 text-xs text-zinc-400">
                Signals collected from the development ecosystem
              </p>
            </div>

            <div className="p-5 sm:p-6">
              {evidenceItems.length === 0 ? (
                <EmptyState
                  icon={<Database className="h-5 w-5" />}
                  title="No evidence collected yet"
                  description="Logs, traces, metrics, database state, and source-code evidence will appear here when the investigation backend collects them."
                />
              ) : (
                <div className="space-y-3">
                  {evidenceItems.map((item) => (
                    <EvidenceItem
                      key={item.id}
                      title={item.title}
                      source={item.source}
                      description={item.description}
                      status={item.status}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Hypotheses */}
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-5 py-5 sm:px-6">
              <h2 className="text-sm font-semibold">Hypotheses</h2>

              <p className="mt-1 text-xs text-zinc-400">
                Candidate explanations ranked by supporting evidence
              </p>
            </div>

            <div className="p-5 sm:p-6">
              {hypotheses.length === 0 ? (
                <EmptyState
                  icon={<ShieldCheck className="h-5 w-5" />}
                  title="Hypothesis engine is waiting"
                  description="Once sufficient evidence is collected, DevRescue can rank probable root causes."
                />
              ) : (
                <div className="space-y-3">
                  {hypotheses.map((hypothesis) => (
                    <div
                      key={hypothesis.id}
                      className="rounded-lg border border-zinc-200 p-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-sm font-medium">
                            {hypothesis.name}
                          </div>

                          <div className="mt-1 text-xs text-zinc-400">
                            {hypothesis.category}
                          </div>
                        </div>

                        <div className="shrink-0 text-sm font-semibold">
                          {Math.round(
                            (hypothesis.confidence ?? 0) * 100
                          )}
                          %
                        </div>
                      </div>

                      <p className="mt-3 text-xs leading-5 text-zinc-500">
                        {hypothesis.explanation}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </main>

        {/* Right rail */}
        <aside className="min-w-0 space-y-6">
          <section className="rounded-xl border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-5 py-4">
              <h2 className="text-sm font-semibold">
                Investigation lifecycle
              </h2>
            </div>

            <div className="p-5">
              <Lifecycle
                currentStage={investigation.currentStage || "Created"}
              />
            </div>
          </section>

          <section className="rounded-xl border border-zinc-200 bg-zinc-950 text-white">
            <div className="p-5">
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-zinc-400">
                <ShieldCheck className="h-3.5 w-3.5" />
                Safety boundary
              </div>

              <h3 className="mt-4 text-sm font-semibold">
                Human-controlled remediation
              </h3>

              <p className="mt-2 text-xs leading-5 text-zinc-400">
                Investigation can be autonomous. Production changes and
                GitHub remediation require explicit human approval.
              </p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

/* ============================================================
   Reusable UI components
============================================================ */

function Metric({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="min-w-0 rounded-xl border border-zinc-200 bg-white p-5">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-zinc-400">
        {label}
      </div>

      <div
        title={value}
        className={`mt-3 break-words text-sm font-medium ${
          mono ? "font-mono text-xs" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const active = status === "investigating";

  return (
    <div
      className={`flex w-fit shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${
        active
          ? "border-blue-200 bg-blue-50 text-blue-700"
          : "border-zinc-200 bg-white text-zinc-600"
      }`}
    >
      {active ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : (
        <CheckCircle2 className="h-3.5 w-3.5" />
      )}

      {status.replaceAll("_", " ")}
    </div>
  );
}

function ActivityItem({
  tool,
  action,
  status,
  timestamp,
}: {
  tool: string;
  action: string;
  status: string;
  timestamp: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-100">
        <Terminal className="h-4 w-4 text-zinc-600" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="break-words text-sm font-medium">{tool}</div>

          <div className="text-[10px] text-zinc-400">{timestamp}</div>
        </div>

        <p className="mt-1 break-words text-xs leading-5 text-zinc-500">
          {action}
        </p>

        <div className="mt-2 text-[10px] uppercase tracking-widest text-zinc-400">
          {status}
        </div>
      </div>
    </div>
  );
}

function EvidenceItem({
  title,
  source,
  description,
  status,
}: {
  title: string;
  source: string;
  description: string;
  status: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="break-words text-sm font-medium">{title}</div>

          <div className="mt-1 flex items-center gap-2 break-words text-xs text-zinc-400">
            <GitBranch className="h-3 w-3 shrink-0" />
            {source}
          </div>
        </div>

        <span className="shrink-0 rounded-full bg-zinc-100 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-zinc-500">
          {status}
        </span>
      </div>

      <p className="mt-3 break-words text-xs leading-5 text-zinc-500">
        {description}
      </p>
    </div>
  );
}

function EmptyState({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-zinc-200 px-6 py-10 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-100 text-zinc-500">
        {icon}
      </div>

      <h3 className="mt-4 text-sm font-medium">{title}</h3>

      <p className="mt-1 max-w-sm text-xs leading-5 text-zinc-400">
        {description}
      </p>
    </div>
  );
}

function Lifecycle({ currentStage }: { currentStage: string }) {
  const stages = [
    { name: "Created", label: "Incident created", icon: CheckCircle2 },
    { name: "Collecting evidence", label: "Collecting evidence", icon: Search },
    { name: "Root cause", label: "Root cause", icon: ShieldCheck },
    { name: "Remediation", label: "Remediation", icon: GitBranch },
    { name: "Validation", label: "Validation", icon: CheckCircle2 },
    { name: "Human approval", label: "Human approval", icon: ShieldCheck },
    { name: "GitHub PR", label: "GitHub PR", icon: GitBranch },
  ];

  const normalizedStage = currentStage.trim().toLowerCase();

  const aliases: Record<string, string> = {
    created: "created",
    investigating: "collecting evidence",
    "evidence collection": "collecting evidence",
    "collecting evidence": "collecting evidence",
    "root cause analysis": "root cause",
    "root cause identified": "root cause",
    "generating remediation": "remediation",
    "generating patch": "remediation",
    "awaiting approval": "human approval",
    "creating pull request": "github pr",
    completed: "github pr",
  };

  const resolvedStage = aliases[normalizedStage] ?? normalizedStage;

  const currentIndex = stages.findIndex(
    (stage) => stage.name.toLowerCase() === resolvedStage
  );

  return (
    <div className="space-y-1">
      {stages.map((stage, index) => {
        const Icon = stage.icon;
        const active = index === currentIndex;
        const complete = currentIndex > index;

        return (
          <div key={stage.name} className="flex items-center gap-3 py-2">
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                complete
                  ? "bg-emerald-100 text-emerald-600"
                  : active
                    ? "bg-zinc-950 text-white"
                    : "bg-zinc-100 text-zinc-400"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
            </div>

            <span
              className={`text-xs ${
                active
                  ? "font-medium text-zinc-950"
                  : complete
                    ? "text-zinc-600"
                    : "text-zinc-400"
              }`}
            >
              {stage.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
