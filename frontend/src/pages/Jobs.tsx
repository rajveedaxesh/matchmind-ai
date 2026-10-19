import { useMemo, useState } from "react";
import { api } from "../api";
import { JobCard } from "../components/JobCard";
import { Empty, ErrorBox, Loading, SyntheticBanner } from "../components/ui";
import { useAsync } from "../lib/useAsync";
import type { Match } from "../types";

const PAGE = 10;

export function Jobs() {
  const [q, setQ] = useState("");
  const [location, setLocation] = useState("");
  const [workMode, setWorkMode] = useState("");
  const [seniority, setSeniority] = useState("");
  const [skill, setSkill] = useState("");
  const [sort, setSort] = useState("id");
  const [page, setPage] = useState(0);
  const reset = () => setPage(0);

  const jobs = useAsync(
    () => api.jobs({ q, location, work_mode: workMode, seniority, skill, sort, limit: PAGE, offset: page * PAGE }),
    [q, location, workMode, seniority, skill, sort, page],
  );
  const recs = useAsync(() => api.recommendations({ limit: 50 }), []);
  const scores = useMemo(() => {
    const m = new Map<number, { match: Match; rank: number }>();
    recs.data?.items.forEach((r) => m.set(r.job.id, { match: r.match, rank: r.rank }));
    return m;
  }, [recs.data]);

  const total = jobs.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE));
  return (
    <>
      <div className="page-head"><div><h1>Job discovery</h1><p>Filter fictional listings; each card shows your personal match score.</p></div></div>
      <SyntheticBanner />
      <form className="card filters" onSubmit={(e) => e.preventDefault()} aria-label="Job filters" style={{ marginBottom: "1rem" }}>
        <label>Search<input type="search" value={q} placeholder="title, company, skill" onChange={(e) => { setQ(e.target.value); reset(); }} /></label>
        <label>Location<input value={location} placeholder="e.g. Berlin" onChange={(e) => { setLocation(e.target.value); reset(); }} /></label>
        <label>Skill<input value={skill} placeholder="e.g. python" onChange={(e) => { setSkill(e.target.value); reset(); }} /></label>
        <label>Work mode
          <select value={workMode} onChange={(e) => { setWorkMode(e.target.value); reset(); }}>
            <option value="">Any</option><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="onsite">Onsite</option>
          </select></label>
        <label>Seniority
          <select value={seniority} onChange={(e) => { setSeniority(e.target.value); reset(); }}>
            <option value="">Any</option><option value="junior">Junior</option><option value="mid">Mid</option><option value="senior">Senior</option><option value="lead">Lead</option>
          </select></label>
        <label>Sort
          <select value={sort} onChange={(e) => { setSort(e.target.value); reset(); }}>
            <option value="id">Default</option><option value="title">Title</option><option value="salary_desc">Salary (high)</option><option value="newest">Newest</option>
          </select></label>
      </form>
      {jobs.error && <ErrorBox message={jobs.error} onRetry={jobs.reload} />}
      {jobs.loading && !jobs.data && <Loading what="Loading jobs" />}
      {jobs.data && <p className="muted" aria-live="polite">{total} job{total === 1 ? "" : "s"} found</p>}
      {jobs.data && total === 0 && <Empty>No jobs match these filters. Try removing one.</Empty>}
      <ul className="list">
        {jobs.data?.items.map((j) => {
          const s = scores.get(j.id);
          return <JobCard key={`${j.id}-${j.application_status}`} job={j} match={s?.match} onChanged={jobs.reload} />;
        })}
      </ul>
      {total > PAGE && (
        <div className="row" style={{ justifyContent: "center", marginTop: "1rem" }}>
          <button className="btn" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
          <span className="muted">Page {page + 1} of {pages}</span>
          <button className="btn" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      )}
    </>
  );
}
