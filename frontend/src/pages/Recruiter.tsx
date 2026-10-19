import { useState, type FormEvent } from "react";
import { ApiError, api } from "../api";
import { Empty, ErrorBox, Loading, MatchDetail, ScoreBadge, SkillChips, SyntheticBanner } from "../components/ui";
import { parseList, rankingReason, sortedContributions } from "../lib/format";
import { useAsync } from "../lib/useAsync";
import type { CandidateRanking, Method, RecruiterResponse } from "../types";

function CandidateCard({ item, next }: { item: CandidateRanking; next: CandidateRanking | null }) {
  const [open, setOpen] = useState(false);
  const m = item.match;
  const top = sortedContributions(m).slice(0, 3);
  return (
    <li className="card item">
      <div className="rank" aria-label={`Rank ${item.rank}`}>{item.rank}</div>
      <div>
        <h3>{item.candidate.display_name} <small>(fictional)</small></h3>
        <p className="meta">{item.candidate.headline}{item.candidate.years_experience != null ? ` · ${item.candidate.years_experience} yrs` : ""}{item.candidate.location ? ` · ${item.candidate.location}` : ""}</p>
        <p><span className="lbl">Matched</span> <SkillChips items={m.matched_required} kind="match" partial={m.partial_required} /></p>
        <p><span className="lbl">Missing</span> <SkillChips items={m.missing_required} kind="missing" /></p>
        <p className="meta">Top contributors: {top.map((c) => `${c.label} +${c.contribution.toFixed(1)}`).join(" · ")}</p>
        <p className="why"><strong>Why this rank:</strong> {rankingReason(m, next?.match ?? null)}</p>
        {open && <MatchDetail match={m} />}
      </div>
      <div className="actions">
        <ScoreBadge score={m.score} label={m.label} />
        <button className="btn btn-sm" aria-expanded={open} onClick={() => setOpen(!open)}>{open ? "Hide" : "Show"} breakdown</button>
      </div>
    </li>
  );
}

export function Recruiter() {
  const jobs = useAsync(() => api.jobs({ limit: 100, sort: "title" }), []);
  const [mode, setMode] = useState<"stored" | "custom">("stored");
  const [jobId, setJobId] = useState("");
  const [method, setMethod] = useState<Method>("hybrid");
  const [custom, setCustom] = useState({ title: "", description: "", required: "", preferred: "" });
  const [result, setResult] = useState<RecruiterResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function run(e: FormEvent) {
    e.preventDefault();
    setError(null); setLoading(true);
    try {
      const base = { limit: 15, method };
      const res = mode === "stored"
        ? await api.recruiterMatch({ ...base, job_id: Number(jobId) })
        : await api.recruiterMatch({ ...base, job: { title: custom.title, description: custom.description, required_skills: parseList(custom.required), preferred_skills: parseList(custom.preferred) } });
      setResult(res);
    } catch (err) {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Matching failed");
    } finally { setLoading(false); }
  }

  const ready = mode === "stored" ? jobId !== "" : custom.title.trim().length >= 2 && custom.description.trim().length >= 20;
  return (
    <>
      <div className="page-head"><div><h1>Recruiter matching</h1><p>Rank the fictional candidate pool for a job. Rankings use skills, text, experience, role and stated preferences only.</p></div></div>
      <SyntheticBanner text="All candidates are fictional. Names are display labels only and are never used for scoring; no protected attributes exist in the data." />
      <form className="card stack" onSubmit={run} aria-label="Recruiter matching form" style={{ marginBottom: "1.2rem" }}>
        <div className="row">
          <div className="seg" role="group" aria-label="Job source">
            <button type="button" aria-pressed={mode === "stored"} onClick={() => setMode("stored")}>Select a job</button>
            <button type="button" aria-pressed={mode === "custom"} onClick={() => setMode("custom")}>Enter a description</button>
          </div>
          <div className="seg" role="group" aria-label="Ranking method">
            <button type="button" aria-pressed={method === "hybrid"} onClick={() => setMethod("hybrid")}>Hybrid</button>
            <button type="button" aria-pressed={method === "tfidf"} onClick={() => setMethod("tfidf")}>TF-IDF baseline</button>
          </div>
        </div>
        {mode === "stored" ? (
          <label>Job
            <select value={jobId} onChange={(e) => setJobId(e.target.value)}>
              <option value="">Choose a job...</option>
              {jobs.data?.items.map((j) => <option key={j.id} value={j.id}>{j.title} - {j.company}</option>)}
            </select>
          </label>
        ) : (
          <>
            <label>Job title<input value={custom.title} onChange={(e) => setCustom({ ...custom, title: e.target.value })} /></label>
            <label>Description <span className="hint">at least 20 characters</span><textarea value={custom.description} onChange={(e) => setCustom({ ...custom, description: e.target.value })} /></label>
            <div className="form-grid">
              <label>Required skills <span className="hint">comma-separated; leave blank to infer from the text</span><input value={custom.required} onChange={(e) => setCustom({ ...custom, required: e.target.value })} /></label>
              <label>Preferred skills<input value={custom.preferred} onChange={(e) => setCustom({ ...custom, preferred: e.target.value })} /></label>
            </div>
          </>
        )}
        <div><button className="btn btn-primary" type="submit" disabled={!ready || loading}>{loading ? "Ranking..." : "Rank candidates"}</button></div>
      </form>
      {error && <ErrorBox message={error} />}
      {loading && <Loading what="Ranking candidates" />}
      {result && (
        <>
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h2>{result.job.title}{result.job.company ? ` - ${result.job.company}` : ""}</h2>
            <p><span className="lbl">Required</span> <SkillChips items={result.job.required_skills} kind="neutral" />{result.job.skills_inferred_from_text && <small> (inferred from the description)</small>}</p>
            <p className="muted">Showing {result.total_returned} of {result.total_candidates} candidates ranked by <strong>{result.method === "hybrid" ? "hybrid score" : "TF-IDF similarity"}</strong>.</p>
          </div>
          {result.items.length === 0 ? <Empty>No candidates to show.</Empty> : (
            <ul className="list">{result.items.map((it, i) => <CandidateCard key={it.candidate.id} item={it} next={result.items[i + 1] ?? null} />)}</ul>
          )}
          <p className="disclaimer">{result.disclaimer}</p>
        </>
      )}
    </>
  );
}
