export type IncidentSeverity =
  | "Critical"
  | "High"
  | "Medium"
  | "Low";

export type IncidentStatus =
  | "Open"
  | "Investigating"
  | "Root cause identified"
  | "Resolved";

export interface Incident {
  id: string;
  title: string;
  description: string;
  service: string;
  environment: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  createdAt: string;
}