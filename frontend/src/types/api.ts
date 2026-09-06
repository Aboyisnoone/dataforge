export type InvestigationStatus = "OPEN" | "INVESTIGATING" | "RESOLVED" | "REJECTED";
export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Observation {
    id: string;
    metric: string;
    value: any;
    column: string;
    dataset_version: string;
    description: string;
}

export interface Evidence {
    id: string;
    type: string;
    source: string;
    dataset_version: string;
    metric: string;
    value: any;
    description: string;
}

export interface InvestigationAction {
    type: string;
    target: string;
    rationale: string;
    priority: string;
}

export interface Finding {
    id: string;
    title: string;
    description: string;
    category: string;
    severity: Severity;
    confidence: number;
    impact_score: number;
    column?: string;
    rule?: string;
    observations: Observation[];
    evidence: Evidence[];
}

export interface Resolution {
    root_cause: string;
    resolution_type: string;
    resolved_at: string;
    validation_result: string;
}

export interface TimelineEvent {
    id: string;
    event_type: string;
    source: string;
    entity_id: string;
    description: string;
    metadata: any;
    timestamp: string;
    sequence_number: number;
}

export interface Hypothesis {
    id: string;
    description: string;
    status: string;
    finding_id?: string;
    attribution_id?: string;
}

export interface Investigation {
    id: string;
    title: string;
    description: string;
    dataset_version: string;
    status: InvestigationStatus;
    created_at: string;
    resolution?: Resolution;
    findings: Finding[];
    recommendations: InvestigationAction[];
    timeline: TimelineEvent[];
    hypotheses: Hypothesis[];
    experiments: Experiment[];
}

export interface PaginatedInvestigations {
    items: Investigation[];
    total: number;
    page: number;
    page_size: number;
}
export interface ExperimentResult {
    row_count: number;
    columns: string[];
    sample_rows: any[];
    execution_time_ms: number;
    error_message?: string;
}

export interface Experiment {
    id: string;
    hypothesis_id: string;
    sql_query: string;
    requested_by: string;
    status: string;
    created_at: string;
    completed_at?: string;
    result?: ExperimentResult;
}
