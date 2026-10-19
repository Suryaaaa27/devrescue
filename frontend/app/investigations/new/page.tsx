"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Bot,
  ChevronRight,
  CircleAlert,
  Database,
  GitBranch,
  Server,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { createInvestigation, startInvestigation } from "@/lib/api";

const failureTypes = [
  "Application Error",
  "Database Failure",
  "Infrastructure Failure",
  "Performance Degradation",
  "Unknown",
];

export default function NewInvestigationPage() {
  const router = useRouter();

  const [service, setService] = useState("payment-service");
  const [environment, setEnvironment] = useState("production");
  const [severity, setSeverity] = useState("Critical");
  const [failureType, setFailureType] =
    useState("Application Error");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!description.trim()) {
      setError("Describe what is failing.");
      return;
    }

    setError("");
    setErrorMessage("");
    setLoading(true);

    try {
      /*
       * Step 1:
       * Create the investigation in the backend.
       */
      const investigation =
        await createInvestigation({
          service,
          environment,
          severity,
          failureType,
          description: description.trim(),
          error: error.trim() || undefined,
        });

      /*
       * Step 2:
       * Start the actual investigation.
       */
      await startInvestigation(
        investigation.id
      );

      /*
       * Step 3:
       * Move into the real investigation workspace.
       */
      router.push(
        `/investigations/${investigation.id}`
      );
    } catch (err) {
      console.error(err);

      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Unable to start investigation."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {/* Header */}

      <div>
        <button
          type="button"
          onClick={() => router.back()}
          className="mb-6 flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-950"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>

        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-zinc-950">
            <Bot className="h-5 w-5 text-white" />
          </div>

          <div>
            <div className="mb-1 flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-zinc-400">
              <Sparkles className="h-3.5 w-3.5" />
              DevRescue
            </div>

            <h1 className="text-3xl font-semibold tracking-tight">
              New investigation
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
              Give DevRescue the failure context. The agent
              will investigate the evidence, identify the
              probable root cause, and propose a safe
              remediation.
            </p>
          </div>
        </div>
      </div>

      {/* Workflow */}

      <div className="flex items-center gap-3 rounded-xl border border-zinc-200 bg-white px-5 py-4">
        <WorkflowStep
          number="01"
          title="Describe"
          active
        />

        <ChevronRight className="h-4 w-4 text-zinc-300" />

        <WorkflowStep
          number="02"
          title="Investigate"
        />

        <ChevronRight className="h-4 w-4 text-zinc-300" />

        <WorkflowStep
          number="03"
          title="Root cause"
        />

        <ChevronRight className="h-4 w-4 text-zinc-300" />

        <WorkflowStep
          number="04"
          title="Remediate"
        />
      </div>

      {/* Form */}

      <form
        onSubmit={handleSubmit}
        className="space-y-6"
      >
        <section className="rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-6 py-5">
            <h2 className="text-sm font-semibold">
              Incident context
            </h2>

            <p className="mt-1 text-xs text-zinc-400">
              Tell DevRescue where the failure occurred.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-6 p-6">
            <Field
              label="Service"
              icon={<Server className="h-4 w-4" />}
            >
              <input
                value={service}
                onChange={(event) =>
                  setService(event.target.value)
                }
                placeholder="payment-service"
                className={inputClass}
              />
            </Field>

            <Field
              label="Environment"
              icon={<ShieldCheck className="h-4 w-4" />}
            >
              <select
                value={environment}
                onChange={(event) =>
                  setEnvironment(event.target.value)
                }
                className={inputClass}
              >
                <option value="production">
                  Production
                </option>
                <option value="staging">
                  Staging
                </option>
                <option value="development">
                  Development
                </option>
              </select>
            </Field>

            <Field
              label="Severity"
              icon={<CircleAlert className="h-4 w-4" />}
            >
              <select
                value={severity}
                onChange={(event) =>
                  setSeverity(event.target.value)
                }
                className={inputClass}
              >
                <option>Critical</option>
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
            </Field>

            <Field
              label="Failure type"
              icon={<Database className="h-4 w-4" />}
            >
              <select
                value={failureType}
                onChange={(event) =>
                  setFailureType(event.target.value)
                }
                className={inputClass}
              >
                {failureTypes.map((type) => (
                  <option key={type}>
                    {type}
                  </option>
                ))}
              </select>
            </Field>
          </div>
        </section>

        <section className="rounded-xl border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-6 py-5">
            <h2 className="text-sm font-semibold">
              Failure details
            </h2>

            <p className="mt-1 text-xs text-zinc-400">
              Include the symptoms and anything you already
              know about the failure.
            </p>
          </div>

          <div className="space-y-6 p-6">
            <div>
              <label className="mb-2 block text-sm font-medium text-zinc-800">
                What is happening?
              </label>

              <textarea
                value={description}
                onChange={(event) =>
                  setDescription(event.target.value)
                }
                rows={6}
                placeholder="Example: Payment requests started returning HTTP 500 errors shortly after the latest deployment. Customers are unable to complete checkout."
                className={`${inputClass} resize-none`}
              />

              <p className="mt-2 text-xs text-zinc-400">
                Be specific. Error messages, timing, recent
                deployments, and affected functionality are
                useful evidence.
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-zinc-800">
                Error message{" "}
                <span className="font-normal text-zinc-400">
                  optional
                </span>
              </label>

              <textarea
                value={error}
                onChange={(event) =>
                  setError(event.target.value)
                }
                rows={3}
                placeholder="Example: ConnectionRefusedError: database connection refused"
                className={`${inputClass} resize-none font-mono text-xs`}
              />
            </div>
          </div>
        </section>

        {/* Safety notice */}

        <div className="flex gap-4 rounded-xl border border-amber-200 bg-amber-50 p-5">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

          <div>
            <div className="text-sm font-medium text-amber-950">
              Human approval remains required
            </div>

            <p className="mt-1 text-xs leading-5 text-amber-800">
              DevRescue can investigate and propose a
              remediation, but it cannot apply production
              changes or create a remediation PR without
              human approval.
            </p>
          </div>
        </div>

        {errorMessage && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <div className="font-medium">
              Unable to start investigation
            </div>

            <div className="mt-1 text-xs">
              {errorMessage}
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm font-medium text-zinc-600 transition hover:bg-zinc-50"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-zinc-950 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Bot className="h-4 w-4" />

            {loading
              ? "Starting investigation..."
              : "Start investigation"}

            {!loading && (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-zinc-200 bg-white px-3.5 py-2.5 text-sm text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-zinc-400 focus:ring-2 focus:ring-zinc-100";

function Field({
  label,
  icon,
  children,
}: {
  label: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-2 flex items-center gap-2 text-sm font-medium text-zinc-800">
        <span className="text-zinc-400">
          {icon}
        </span>
        {label}
      </label>

      {children}
    </div>
  );
}

function WorkflowStep({
  number,
  title,
  active = false,
}: {
  number: string;
  title: string;
  active?: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-semibold ${
          active
            ? "bg-zinc-950 text-white"
            : "bg-zinc-100 text-zinc-400"
        }`}
      >
        {number}
      </div>

      <span
        className={`text-xs font-medium ${
          active
            ? "text-zinc-900"
            : "text-zinc-400"
        }`}
      >
        {title}
      </span>
    </div>
  );
}