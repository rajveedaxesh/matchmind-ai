import { useState } from "react";
import { api } from "../api";
import { ErrorBox, Loading, SyntheticBanner } from "../components/ui";
import { fmt } from "../lib/format";
import { useAsync } from "../lib/useAsync";
import type { EvalDirection } from "../types";

function columns(d: EvalDirection) {
  return [...d.ks.map((k) => `precision@${k}`), ...d.ks.map((k) => `recall@${k}`), ...d.ks.map((k) => `ndcg@${k}`), "mrr"];
}

export function Evaluation() {
  const ev = useAsync(() => api.evaluation(), []);
  const [direction, setDirection] = useState("recruiter");
  const d = ev.data?.directions[direction];
  const k = d ? (d.ks.includes(5) ? 5 : d.ks[0]) : 5;
  const focus = `ndcg@${k}`;

  return (
    <>
      <div className="page-head"><div><h1>Model evaluation</h1><p>Ranking quality of each method against synthetic relevance labels, computed live by the backend evaluation code.</p></div></div>
      <SyntheticBanner text="Labels are rule-generated on fictional data. These numbers demonstrate the evaluation pipeline; they are not evidence of real-world hiring accuracy." />
      {ev.loading && !ev.data && <Loading what="Running evaluation" />}
      {ev.error && <ErrorBox message={ev.error} onRetry={ev.reload} />}
      {ev.data && d && (
        <>
          <div className="row" style={{ marginBottom: "1rem" }}>
            <div className="seg" role="group" aria-label="Evaluation direction">
              {Object.keys(ev.data.directions).map((key) => (
                <button key={key} aria-pressed={direction === key} onClick={() => setDirection(key)}>{key === "recruiter" ? "Recruiter (rank candidates)" : "Job seeker (rank jobs)"}</button>
              ))}
            </div>
            <span className="muted">{d.n_queries_evaluated} queries &middot; {ev.data.dataset.n_jobs} jobs &times; {ev.data.dataset.n_candidates} candidates &middot; seed {ev.data.config.seed}</span>
          </div>
          <p>{d.description}</p>
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h2>{focus.toUpperCase()} with 95% bootstrap interval</h2>
            <div className="metric-bars">
              {Object.entries(d.methods).map(([key, m]) => {
                const s = m.metrics[focus];
                return (
                  <div className="metric-row" key={key}>
                    <span>{m.label}</span>
                    <div className="metric-track" role="img" aria-label={`${m.label} ${focus} ${fmt(s.mean)} (95% CI ${fmt(s.ci_low)} to ${fmt(s.ci_high)})`}>
                      <div className="metric-fill" style={{ width: `${s.mean * 100}%` }} />
                      <div className="metric-ci" style={{ left: `${s.ci_low * 100}%`, width: `${Math.max(0, s.ci_high - s.ci_low) * 100}%` }} />
                    </div>
                    <span>{fmt(s.mean)} <small>[{fmt(s.ci_low, 2)}, {fmt(s.ci_high, 2)}]</small></span>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="card table-wrap" style={{ marginBottom: "1rem" }}>
            <h2>All metrics</h2>
            <table>
              <thead><tr><th scope="col">Method</th>{columns(d).map((c) => <th scope="col" key={c}>{c}</th>)}</tr></thead>
              <tbody>
                {Object.entries(d.methods).map(([key, m]) => (
                  <tr key={key} className={key === "hybrid" ? "best" : ""}>
                    <td title={m.description}>{m.label}</td>
                    {columns(d).map((c) => <td key={c}>{fmt(m.metrics[c].mean)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h2>Hybrid vs TF-IDF baseline (paired difference)</h2>
            <ul className="explain">
              {d.paired_comparisons.map((c) => (
                <li key={c.metric}><strong>{c.metric}</strong>: {c.mean_difference >= 0 ? "+" : ""}{fmt(c.mean_difference)} [{fmt(c.ci_low)}, {fmt(c.ci_high)}] &mdash; {c.ci_excludes_zero ? "interval excludes 0 (a consistent difference on this benchmark)" : "interval includes 0 (no reliable difference on this benchmark)"}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h2>How to read this</h2>
            <p className="muted"><strong>Label rule:</strong> {ev.data.dataset.label_definition}</p>
            <ul className="explain">{ev.data.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
            <p className="muted" style={{ fontSize: ".8rem" }}>Generated {ev.data.generated_at} in {ev.data.runtime_seconds}s.</p>
          </div>
        </>
      )}
    </>
  );
}
