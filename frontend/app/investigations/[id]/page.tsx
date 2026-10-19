
import { Suspense } from "react";
import InvestigationWorkspaceClient from "@/components/investigation/InvestigationWorkspaceClient";

export const instant = false;

interface InvestigationPageProps {
  params: Promise<{ id: string }>;
}

export default async function InvestigationPage({
  params,
}: InvestigationPageProps) {
  const { id } = await params;

  return (
    <Suspense
      fallback={
        <div className="flex min-h-[70vh] items-center justify-center text-sm text-zinc-500">
          Loading investigation workspace...
        </div>
      }
    >
      <InvestigationWorkspaceClient id={id} />
    </Suspense>
  );
}
