import { api } from "../api";
import { JobCard } from "../components/JobCard";
import { ErrorBox, Loading, SyntheticBanner } from "../components/ui";
import { useAsync } from "../lib/useAsync";

export function Overview({ go }: { go: (route: string) => void }) {
  const meta = useAsync(() => api.meta(), []);
  const profile = useAsync(() => api.profile(), []);
  const recs = useAsync(() => api.recommendations({ limit: 5 }), []);
  const apps = useAsync(() => api.applications(), []);

  const err = meta.error || profile.error || recs.error;
  return (
    <>
      <div className="page-head">
        <div><h1>Overview</h1><p>Your top matches, profile health and pipeline at a glance.</p></div>
      </div>
      <SyntheticBanner text={meta.data?.data_notice} />
      {err && <ErrorBox message={err} onRetry={() => { meta.reload(); profile.reload(); recs.reload(); }} />}
      <div className="grid grid-stats" style={{ marginBottom: "1rem" }}>
        <div className="card stat"><div className="num">{meta.data?.counts.jobs ?? "-"}</div><div className="lbl">Fictional jobs</div></div>
        <div className="card stat"><div className="num">{meta.data?.counts.candidates ?? "-"}</div><div className="lbl">Fictional candidates</div></div>
        <div className="card stat"><div className="num">{apps.data ? apps.data.items.length : "-"}</div><div className="lbl">Saved / tracked jobs</div></div>
        <div className="card stat"><div className="num">{profile.data ? `${profile.data.completeness.percent}%` : "-"}</div><div className="lbl">Profile complete</div></div>
      </div>
      {profile.data && profile.data.completeness.missing.length > 0 && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <div className="spread">
            <div><h3>Improve your recommendations</h3>
              <ul className="explain">{profile.data.completeness.missing.map((m) => <li key={m}>{m}</li>)}</ul></div>
            <button className="btn btn-primary" onClick={() => go("profile")}>Edit profile</button>
          </div>
        </div>
      )}
      <div className="page-head"><h2>Recommended for you</h2><button className="btn" onClick={() => go("jobs")}>Browse all jobs</button></div>
      {recs.loading && !recs.data && <Loading what="Ranking jobs" />}
      {recs.data?.warnings.map((w) => <p key={w} className="warn-list">{w}</p>)}
      <ul className="list">
        {recs.data?.items.map((r) => <JobCard key={r.job.id} job={r.job} match={r.match} rank={r.rank} onChanged={apps.reload} />)}
      </ul>
      {meta.data && (
        <p className="muted" style={{ marginTop: "1.2rem", fontSize: ".82rem" }}>
          Text similarity uses TF-IDF plus a <strong>{meta.data.embedding_backend}</strong> semantic encoder
          {meta.data.embedding_fallback_reason ? ` (fallback: ${meta.data.embedding_fallback_reason})` : " running locally"}.
        </p>
      )}
    </>
  );
}
