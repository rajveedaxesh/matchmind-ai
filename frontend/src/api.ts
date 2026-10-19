import type {
  ApplicationList, ApplicationItem, ApplicationStatus, EvaluationResult, Job, JobList, Meta, Method,
  Profile, ProfileInput, RecommendationList, JobRecommendation, RecruiterRequest, RecruiterResponse, Candidate,
} from "./types";

export class ApiError extends Error {
  constructor(message: string, public status: number, public fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
  }
}

/** Turn a FastAPI error body (string detail or 422 list) into a readable message + per-field errors. */
export function parseErrorBody(status: number, body: unknown): ApiError {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return new ApiError(detail, status);
  if (Array.isArray(detail)) {
    const fieldErrors: Record<string, string> = {};
    const lines: string[] = [];
    for (const d of detail as { loc?: (string | number)[]; msg?: string }[]) {
      const path = (d.loc ?? []).filter((p) => p !== "body");
      const field = String(path[path.length - 1] ?? "");
      const msg = (d.msg ?? "Invalid value").replace(/^Value error, /, "");
      if (field && !(field in fieldErrors)) fieldErrors[field] = msg;
      lines.push(field ? `${field}: ${msg}` : msg);
    }
    return new ApiError(lines.join("; ") || "Validation failed", status, fieldErrors);
  }
  return new ApiError(`Request failed (${status})`, status);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError("Cannot reach the MatchMind API. Is the backend running on port 8000?", 0);
  }
  if (res.status === 204) return undefined as T;
  let body: unknown = null;
  try { body = await res.json(); } catch { /* non-JSON error body */ }
  if (!res.ok) throw parseErrorBody(res.status, body);
  return body as T;
}

const qs = (params: Record<string, string | number | undefined | null>) => {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  const s = sp.toString();
  return s ? `?${s}` : "";
};

export interface JobFilters {
  q?: string; location?: string; work_mode?: string; seniority?: string; skill?: string;
  sort?: string; limit?: number; offset?: number;
}

export const api = {
  meta: () => request<Meta>("/api/meta"),
  jobs: (f: JobFilters = {}) => request<JobList>(`/api/jobs${qs({ ...f })}`),
  job: (id: number) => request<Job>(`/api/jobs/${id}`),
  profile: () => request<Profile>("/api/profile"),
  saveProfile: (p: ProfileInput) => request<Profile>("/api/profile", { method: "PUT", body: JSON.stringify(p) }),
  recommendations: (opts: { limit?: number; method?: Method; work_mode?: string } = {}) =>
    request<RecommendationList>(`/api/recommendations${qs({ limit: 50, ...opts })}`),
  explain: (jobId: number, method: Method = "hybrid") =>
    request<JobRecommendation>(`/api/recommendations/${jobId}${qs({ method })}`),
  applications: () => request<ApplicationList>("/api/applications"),
  setApplication: (jobId: number, status: ApplicationStatus, notes?: string) =>
    request<ApplicationItem>(`/api/applications/${jobId}`, { method: "PUT", body: JSON.stringify({ status, notes }) }),
  removeApplication: (jobId: number) => request<void>(`/api/applications/${jobId}`, { method: "DELETE" }),
  candidates: () => request<Candidate[]>("/api/candidates"),
  recruiterMatch: (req: RecruiterRequest) =>
    request<RecruiterResponse>("/api/recruiter/match", { method: "POST", body: JSON.stringify(req) }),
  evaluation: () => request<EvaluationResult>("/api/evaluation"),
};
