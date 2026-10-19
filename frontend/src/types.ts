// Mirrors backend/app/schemas.py. Keep in sync when the API changes.
export type WorkMode = "remote" | "hybrid" | "onsite";
export type Seniority = "junior" | "mid" | "senior" | "lead";
export type Method = "hybrid" | "tfidf";
export type ApplicationStatus = "saved" | "applied" | "interviewing" | "offer" | "rejected" | "withdrawn";

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  "saved", "applied", "interviewing", "offer", "rejected", "withdrawn",
];

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  work_mode: WorkMode;
  employment_type: string;
  seniority: Seniority | null;
  min_years: number | null;
  max_years: number | null;
  salary_min: number | null;
  salary_max: number | null;
  role_family: string | null;
  description: string;
  required_skills: string[];
  preferred_skills: string[];
  is_synthetic: boolean;
  application_status: ApplicationStatus | null;
}

export interface JobList { items: Job[]; total: number; limit: number; offset: number }

export interface Candidate {
  id: number;
  display_name: string;
  headline: string;
  location: string | null;
  years_experience: number | null;
  skills: string[];
  summary: string;
  desired_titles: string[];
  preferred_locations: string[];
  preferred_work_modes: WorkMode[];
  open_to_relocation: boolean;
  is_synthetic: boolean;
}

export interface Profile extends Candidate {
  completeness: { percent: number; missing: string[] };
}

export interface ProfileInput {
  display_name?: string | null;
  headline: string;
  location?: string | null;
  years_experience?: number | null;
  skills: string[];
  summary: string;
  desired_titles: string[];
  preferred_locations: string[];
  preferred_work_modes: WorkMode[];
  open_to_relocation: boolean;
}

export interface ComponentScore {
  key: string;
  label: string;
  score: number;
  weight: number;
  contribution: number;
  applicable: boolean;
  detail: string;
}

export interface PartialSkill { required: string; via: string }

export interface Match {
  score: number;
  label: string;
  summary: string;
  method: Method;
  components: Record<string, ComponentScore>;
  matched_required: string[];
  partial_required: PartialSkill[];
  missing_required: string[];
  matched_preferred: string[];
  partial_preferred: PartialSkill[];
  missing_preferred: string[];
  top_shared_terms: string[];
  explanations: string[];
  disclaimer: string;
}

export interface JobRecommendation { rank: number; job: Job; match: Match }
export interface RecommendationList {
  method: Method;
  total_scored: number;
  total_returned: number;
  items: JobRecommendation[];
  weights: Record<string, number>;
  warnings: string[];
  disclaimer: string;
}

export interface ApplicationItem {
  job: Job;
  status: ApplicationStatus;
  notes: string | null;
  updated_at: string;
  match: Match | null;
}
export interface ApplicationList { items: ApplicationItem[]; counts: Record<string, number> }

export interface AdHocJob {
  title: string;
  description: string;
  company?: string;
  location?: string;
  required_skills: string[];
  preferred_skills: string[];
}

export interface RecruiterRequest {
  job_id?: number;
  job?: AdHocJob;
  limit?: number;
  method?: Method;
  min_score?: number;
}

export interface CandidateRanking { rank: number; candidate: Candidate; match: Match }
export interface RecruiterResponse {
  job: {
    id: number | null; title: string; company: string | null;
    required_skills: string[]; preferred_skills: string[]; skills_inferred_from_text: boolean;
  };
  method: Method;
  total_candidates: number;
  total_returned: number;
  items: CandidateRanking[];
  weights: Record<string, number>;
  disclaimer: string;
}

export interface Meta {
  app: string;
  version: string;
  synthetic_data: boolean;
  data_notice: string;
  disclaimer: string;
  counts: Record<string, number>;
  weights: Record<string, number>;
  component_labels: Record<string, string>;
  embedding_backend: string;
  embedding_fallback_reason: string | null;
}

export interface MetricStat { mean: number; ci_low: number; ci_high: number }
export interface EvalMethod { label: string; description: string; metrics: Record<string, MetricStat> }
export interface EvalComparison {
  metric: string; a: string; b: string; mean_difference: number;
  ci_low: number; ci_high: number; ci_excludes_zero: boolean;
}
export interface EvalDirection {
  description: string;
  n_queries: number;
  n_queries_evaluated: number;
  ks: number[];
  methods: Record<string, EvalMethod>;
  paired_comparisons: EvalComparison[];
}
export interface EvaluationResult {
  generated_at: string;
  runtime_seconds: number;
  synthetic: boolean;
  config: { seed: number; generated_per_family: number; ks: number[]; relevance_threshold: number };
  dataset: {
    n_jobs: number; n_candidates: number; n_labelled_pairs: number;
    grade_distribution: Record<string, number>; label_definition: string;
  };
  directions: Record<string, EvalDirection>;
  caveats: string[];
}
