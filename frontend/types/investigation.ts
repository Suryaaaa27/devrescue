export type InvestigationStatus =
  | "created"
  | "investigating"
  | "root_cause_identified"
  | "remediation_proposed"
  | "patch_generated"
  | "validation"
  | "awaiting_approval"
  | "completed"
  | "failed";

export type EvidenceStatus =
  | "supporting"
  | "contradicting"
  | "neutral";

export interface InvestigationInput {
  service: string;
  environment: string;
  severity: string;
  failureType: string;
  description: string;
  error?: string;
}

export interface InvestigationSummary {
  id: string;
  incidentId?: string;
  service: string;
  environment: string;
  status: InvestigationStatus;
  confidence: number;
  currentStage: string;
  createdAt: string;
  updatedAt: string;
}

export interface InvestigationEvidence {
  id: string;
  source: string;
  type: string;
  title: string;
  description: string;
  status: EvidenceStatus;
  timestamp?: string;
  metadata?: Record<string, unknown>;
}

export interface InvestigationHypothesis {
  id: string;
  name: string;
  category: string;
  explanation: string;
  confidence: number;
  supportingEvidence: string[];
  contradictingEvidence: string[];
  missingEvidence: string[];
  selected: boolean;
}

export interface InvestigationTimelineItem {
  id: string;
  title: string;
  description: string;
  status: "pending" | "active" | "complete" | "failed";
  timestamp?: string;
}

export interface AgentActivity {
  id: string;
  tool: string;
  action: string;
  status: "running" | "completed" | "failed";
  timestamp: string;
}

export interface RootCause {
  title: string;
  explanation: string;
  confidence: number;
  causalChain: string[];
  suspectedCommit?: {
    sha: string;
    message: string;
  };
}

export interface RemediationAction {
  actionType: string;
  description: string;
  target?: string;
  rationale: string;
  patchable: boolean;
  requiresApproval: boolean;
}

export interface RemediationProposal {
  summary: string;
  rationale: string;
  actions: RemediationAction[];
  affectedFiles: string[];
  riskLevel: string;
  confidence: number;
  requiresHumanApproval: boolean;
  patchGenerationAllowed: boolean;
  validationRequirements: string[];
  safetyConstraints: string[];
}

export type Incident = Record<string, unknown>;

export interface InvestigationDetail extends InvestigationSummary {
  incident?: Incident;
  evidence: InvestigationEvidence[];
  hypotheses: InvestigationHypothesis[];
  timeline: InvestigationTimelineItem[];
  activity: AgentActivity[];
  rootCause?: RootCause;
  remediation?: RemediationProposal;
}