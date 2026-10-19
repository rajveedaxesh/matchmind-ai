import { api } from "../api";
import { JobCard } from "../components/JobCard";
import { Empty, ErrorBox, Loading } from "../components/ui";
import { titleCase } from "../lib/format";
import { useAsync } from "../lib/useAsync";
import { APPLICATION_STATUSES } from "../types";

export function Applications() {
  const apps = useAsync(() => api.applications(), []);
  return (
    <>
      <div className="page-head"><div><h1>Saved jobs & applications</h1><p>Track each job through your pipeline. Changing a status here updates the backend.</p></div></div>
      {apps.error && <ErrorBox message={apps.error} onRetry={apps.reload} />}
      {apps.loading && !apps.data && <Loading />}
      {apps.data && apps.data.items.length === 0 && <Empty>Nothing saved yet. Use the status menu on any job to save it.</Empty>}
      {apps.data && apps.data.items.length > 0 && (
        <>
          <div className="row" style={{ marginBottom: "1rem" }}>
            {APPLICATION_STATUSES.map((s) => <span key={s} className={`status status-${s}`}>{titleCase(s)}: {apps.data!.counts[s] ?? 0}</span>)}
          </div>
          <ul className="list">
            {apps.data.items.map((a) => <JobCard key={`${a.job.id}-${a.status}`} job={{ ...a.job, application_status: a.status }} match={a.match ?? undefined} onChanged={apps.reload} />)}
          </ul>
        </>
      )}
    </>
  );
}
