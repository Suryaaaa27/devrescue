import type {
  InvestigationDetail,
  InvestigationInput,
  InvestigationSummary,
} from "@/types/investigation";

import type { Incident } from "@/types/incident";

const API_URL =
  process.env.NEXT_PUBLIC_DEVRESCUE_API_URL ||
  "http://localhost:8002";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_URL}${path}`;

  let response: Response;

  try {
    response = await fetch(url, {
      ...options,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      cache: "no-store",
    });
  } catch (error) {
    console.error("DevRescue API connection failed:", {
      url,
      error,
    });

    throw new Error(
      `Cannot connect to DevRescue API at ${API_URL}. Make sure the backend is running on port 8002.`
    );
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const body = await response.json();

      if (body?.detail) {
        message = body.detail;
      }
    } catch {
      // Keep default message.
    }

    throw new ApiError(message, response.status);
  }

  return response.json();
}

/* ============================================================
   INCIDENTS
============================================================ */

export async function getIncidents(): Promise<Incident[]> {
  return request<Incident[]>("/api/incidents");
}

export async function getIncident(
  incidentId: string
): Promise<Incident> {
  return request<Incident>(
    `/api/incidents/${encodeURIComponent(incidentId)}`
  );
}

/* ============================================================
   INVESTIGATIONS
============================================================ */

export async function getInvestigations(): Promise<
  InvestigationSummary[]
> {
  return request<InvestigationSummary[]>(
    "/api/investigations"
  );
}

export async function getInvestigation(
  investigationId: string
): Promise<InvestigationDetail> {
  return request<InvestigationDetail>(
    `/api/investigations/${encodeURIComponent(
      investigationId
    )}`
  );
}

export async function createInvestigation(
  input: InvestigationInput
): Promise<InvestigationSummary> {
  return request<InvestigationSummary>(
    "/api/investigations",
    {
      method: "POST",
      body: JSON.stringify(input),
    }
  );
}

export async function startInvestigation(
  investigationId: string
): Promise<{
  id: string;
  status: string;
  currentStage: string;
}> {
  return request(
    `/api/investigations/${encodeURIComponent(
      investigationId
    )}/start`,
    {
      method: "POST",
    }
  );
}