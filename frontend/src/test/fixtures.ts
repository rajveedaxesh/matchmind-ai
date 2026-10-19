import type { Job, Match, ComponentScore, Profile, RecruiterResponse, EvaluationResult } from "../types";

export const comp = (key: string, label: string, score: number, weight: number, applicable = true): ComponentScore => ({
  key, label, score, weight, contribution: applicable ? +(score * weight).toFixed(1) : 0, applicable,
  detail: applicable ? `${label} detail` : "Not scored: missing data.",
});

export function makeMatch(score = 82, over: Partial<Match> = {}): Match {
  return {
    score, label: "Strong fit", summary: `Strong fit (${score}/100). Strongest on required skills.`, method: "hybrid",
    components: {
      required_skills: comp("required_skills", "Required skills", 90, 0.4),
      preferred_skills: comp("preferred_skills", "Preferred skills", 50, 0.1),
      text_similarity: comp("text_similarity", "Text similarity", 70, 0.3),
      role_alignment: comp("role_alignment", "Role alignment", 80, 0.2),
      experience: comp("experience", "Experience fit", 0, 0, false),
      location: comp("location", "Location & work mode", 0, 0, false),
    },
    matched_required: ["python", "sql"], partial_required: [{ required: "kubernetes", via: "docker" }],
    missing_required: ["rust"], matched_preferred: ["redis"], partial_preferred: [], missing_preferred: ["kafka"],
    top_shared_terms: ["pipelines"], explanations: ["Matches 2 of 4 required skills.", "Experience was not scored."],
    disclaimer: "Match scores are heuristic fit indicators. They are NOT probabilities of being hired.", ...over,
  };
}

export const makeJob = (id: number, over: Partial<Job> = {}): Job => ({
  id, title: `Job ${id}`, company: "Acme (fictional)", location: "Berlin", work_mode: "remote", employment_type: "full-time",
  seniority: "mid", min_years: 2, max_years: 5, salary_min: 80000, salary_max: 100000, role_family: "data",
  description: "A fictional job description long enough.", required_skills: ["python", "sql"], preferred_skills: ["redis"],
  is_synthetic: true, application_status: null, ...over,
});

export const profile: Profile = {
  id: 99, display_name: "Demo Seeker", headline: "Data Engineer", location: "Berlin", years_experience: 4,
  skills: ["Python", "SQL"], summary: "Builds data pipelines with Python and SQL for analytics teams.",
  desired_titles: ["Data Engineer"], preferred_locations: ["Berlin"], preferred_work_modes: ["remote"],
  open_to_relocation: false, is_synthetic: true, completeness: { percent: 80, missing: ["Add at least 3 skills"] },
};

export const recruiterResponse: RecruiterResponse = {
  job: { id: 1, title: "Job 1", company: "Acme (fictional)", required_skills: ["python", "sql"], preferred_skills: [], skills_inferred_from_text: false },
  method: "hybrid", total_candidates: 15, total_returned: 2, weights: {}, disclaimer: "NOT probabilities of being hired.",
  items: [
    { rank: 1, match: makeMatch(88), candidate: { id: 1, display_name: "Avery Test", headline: "Senior Data Engineer", location: "Berlin", years_experience: 6, skills: [], summary: "", desired_titles: [], preferred_locations: [], preferred_work_modes: [], open_to_relocation: false, is_synthetic: true } },
    { rank: 2, match: makeMatch(61, { missing_required: ["airflow"] }), candidate: { id: 2, display_name: "Blake Test", headline: "Analyst", location: null, years_experience: 2, skills: [], summary: "", desired_titles: [], preferred_locations: [], preferred_work_modes: [], open_to_relocation: false, is_synthetic: true } },
  ],
};

const metrics = (v: number) => Object.fromEntries(
  ["precision@3", "precision@5", "recall@3", "recall@5", "ndcg@3", "ndcg@5", "mrr"].map((k) => [k, { mean: v, ci_low: v - 0.05, ci_high: v + 0.05 }]),
);
export const evaluation: EvaluationResult = {
  generated_at: "2026-01-01T00:00:00+00:00", runtime_seconds: 1.2, synthetic: true,
  config: { seed: 42, generated_per_family: 8, ks: [3, 5], relevance_threshold: 2 },
  dataset: { n_jobs: 32, n_candidates: 122, n_labelled_pairs: 3904, grade_distribution: { "0": 1 }, label_definition: "grade = rule over latent skills." },
  caveats: ["All data are synthetic.", "Labels share concepts with the hybrid scorer."],
  directions: {
    recruiter: {
      description: "Recruiter task: for each job, rank all candidates.", n_queries: 32, n_queries_evaluated: 32, ks: [3, 5],
      methods: {
        random: { label: "Random (seeded)", description: "floor", metrics: metrics(0.1) },
        tfidf: { label: "TF-IDF baseline", description: "tfidf", metrics: metrics(0.8) },
        hybrid: { label: "Hybrid (MatchMind)", description: "hybrid", metrics: metrics(0.85) },
      },
      paired_comparisons: [{ metric: "ndcg@5", a: "hybrid", b: "tfidf", mean_difference: 0.05, ci_low: -0.01, ci_high: 0.1, ci_excludes_zero: false }],
    },
    seeker: {
      description: "Job-seeker task: for each candidate, rank all jobs.", n_queries: 122, n_queries_evaluated: 122, ks: [3, 5],
      methods: { random: { label: "Random (seeded)", description: "floor", metrics: metrics(0.1) }, tfidf: { label: "TF-IDF baseline", description: "t", metrics: metrics(0.9) }, hybrid: { label: "Hybrid (MatchMind)", description: "h", metrics: metrics(0.95) } },
      paired_comparisons: [{ metric: "ndcg@5", a: "hybrid", b: "tfidf", mean_difference: 0.05, ci_low: 0.02, ci_high: 0.08, ci_excludes_zero: true }],
    },
  },
};

type Handler = (url: URL, init?: RequestInit) => { status?: number; body?: unknown } | undefined;

/** Install a fetch mock; `handler` returns a response or undefined (-> 404). Returns the call log. */
export function mockFetch(handler: Handler) {
  const calls: { url: URL; init?: RequestInit }[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://localhost");
    calls.push({ url, init });
    const r = handler(url, init) ?? { status: 404, body: { detail: "not found" } };
    const status = r.status ?? 200;
    return { ok: status < 400, status, json: async () => r.body } as Response;
  }));
  return calls;
}
