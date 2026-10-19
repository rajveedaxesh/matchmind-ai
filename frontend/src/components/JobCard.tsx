import { useState } from "react";
import { api } from "../api";
import { formatSalary, formatYears, titleCase } from "../lib/format";
import { useAsync } from "../lib/useAsync";
import { APPLICATION_STATUSES, type ApplicationStatus, type Job, type Match } from "../types";
import { ErrorBox, Loading, MatchDetail, Modal, ScoreBadge, SkillChips } from "./ui";

function JobModal({ job, match, onClose }: { job: Job; match?: Match; onClose: () => void }) {
  const fetched = useAsync(() => (match ? Promise.resolve(null) : api.explain(job.id)), [job.id, match]);
  const shown = match ?? fetched.data?.match;
  return (
    <Modal title={`${job.title} - ${job.company}`} onClose={onClose}>
      <p className="meta">{job.location} &middot; {titleCase(job.work_mode)} &middot; {job.employment_type}{formatSalary(job) ? ` · ${formatSalary(job)}` : ""}</p>
      <p>{job.description}</p>
      <p><span className="lbl">Required</span> <SkillChips items={job.required_skills} kind="neutral" /></p>
      <p><span className="lbl">Preferred</span> <SkillChips items={job.preferred_skills} kind="neutral" /></p>
      <h2 style={{ marginTop: "1.2rem" }}>How you match</h2>
      {!shown && fetched.loading && <Loading what="Scoring" />}
      {fetched.error && <ErrorBox message={fetched.error} onRetry={fetched.reload} />}
      {shown && <MatchDetail match={shown} />}
    </Modal>
  );
}

interface Props {
  job: Job;
  match?: Match;
  rank?: number;
  onChanged?: () => void;
}

export function JobCard({ job, match, rank, onChanged }: Props) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<ApplicationStatus | "">(job.application_status ?? "");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function change(next: string) {
    setBusy(true); setErr(null);
    const prev = status;
    try {
      if (next === "") await api.removeApplication(job.id);
      else await api.setApplication(job.id, next as ApplicationStatus);
      setStatus(next as ApplicationStatus | "");
      onChanged?.();
    } catch (e) {
      setStatus(prev);
      setErr(e instanceof Error ? e.message : "Could not update");
    } finally { setBusy(false); }
  }

  return (
    <li className="card item">
      {rank != null ? <div className="rank" aria-label={`Rank ${rank}`}>{rank}</div> : <div />}
      <div>
        <h3>{job.title}</h3>
        <p className="meta">{job.company} &middot; {job.location} &middot; {titleCase(job.work_mode)}
          {job.seniority ? ` · ${titleCase(job.seniority)}` : ""}{formatYears(job) ? ` · ${formatYears(job)}` : ""}{formatSalary(job) ? ` · ${formatSalary(job)}` : ""}</p>
        <SkillChips items={job.required_skills.slice(0, 6)} kind="neutral" />
        {match && <p className="why">{match.summary}</p>}
        {err && <p className="field-error" role="alert">{err}</p>}
      </div>
      <div className="actions">
        {match && <ScoreBadge score={match.score} label={match.label} />}
        <button className="btn btn-sm" onClick={() => setOpen(true)}>Why this match?</button>
        <label className="hint">
          <span className="sr-only" style={{ position: "absolute", left: -9999 }}>Application status for {job.title}</span>
          <select aria-label={`Application status for ${job.title}`} value={status} disabled={busy} onChange={(e) => change(e.target.value)}>
            <option value="">Not saved</option>
            {APPLICATION_STATUSES.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
          </select>
        </label>
      </div>
      {open && <JobModal job={job} match={match} onClose={() => setOpen(false)} />}
    </li>
  );
}
