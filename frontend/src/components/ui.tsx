import { useEffect, type ReactNode } from "react";
import type { Match } from "../types";
import { scoreTone, sortedContributions, titleCase } from "../lib/format";

export function ScoreBadge({ score, label, size = "md" }: { score: number; label?: string; size?: "sm" | "md" | "lg" }) {
  const tone = scoreTone(score);
  return (
    <div className={`score score-${tone} score-${size}`} role="img" aria-label={`Match score ${score.toFixed(0)} out of 100${label ? `, ${label}` : ""}`}>
      <span className="score-num">{score.toFixed(0)}</span>
      <span className="score-of">/100</span>
      {label && size !== "sm" && <span className="score-label">{label}</span>}
    </div>
  );
}

export function SkillChips({ items, kind, partial }: { items: string[]; kind: "match" | "missing" | "neutral"; partial?: { required: string; via: string }[] }) {
  if (!items.length && !partial?.length) return <span className="muted">none</span>;
  return (
    <span className="chips">
      {items.map((s) => <span key={s} className={`chip chip-${kind}`}>{s}</span>)}
      {partial?.map((p) => (
        <span key={p.required} className="chip chip-partial" title={`Partial credit: ${p.required} is related to ${p.via}`}>
          {p.required} <small>~ {p.via}</small>
        </span>
      ))}
    </span>
  );
}

export function ComponentBars({ match }: { match: Match }) {
  const comps = Object.values(match.components);
  return (
    <ul className="bars" aria-label="Component scores">
      {comps.map((c) => (
        <li key={c.key} className={c.applicable ? "" : "bar-na"}>
          <div className="bar-head">
            <span>{c.label}</span>
            <span className="bar-meta">
              {c.applicable ? <>{c.score.toFixed(0)}<small> / 100 &middot; weight {(c.weight * 100).toFixed(0)}% &middot; +{c.contribution.toFixed(1)} pts</small></> : <small>not scored</small>}
            </span>
          </div>
          <div className="bar-track" aria-hidden="true"><div className={`bar-fill tone-${scoreTone(c.score)}`} style={{ width: `${c.applicable ? c.score : 0}%` }} /></div>
          <p className="bar-detail">{c.detail}</p>
        </li>
      ))}
    </ul>
  );
}

export function MatchDetail({ match }: { match: Match }) {
  const top = sortedContributions(match)[0];
  return (
    <div className="match-detail">
      <p className="summary">{match.summary}</p>
      {top && <p className="muted">Biggest contributor: <strong>{top.label}</strong> (+{top.contribution.toFixed(1)} points).</p>}
      <h4>Why this score</h4>
      <ul className="explain">{match.explanations.map((e, i) => <li key={i}>{e}</li>)}</ul>
      <h4>Component scores</h4>
      <ComponentBars match={match} />
      <div className="skill-grid">
        <div><h4>Required skills</h4>
          <p><span className="lbl">Matched</span> <SkillChips items={match.matched_required} kind="match" partial={match.partial_required} /></p>
          <p><span className="lbl">Missing</span> <SkillChips items={match.missing_required} kind="missing" /></p>
        </div>
        <div><h4>Preferred skills</h4>
          <p><span className="lbl">Matched</span> <SkillChips items={match.matched_preferred} kind="match" partial={match.partial_preferred} /></p>
          <p><span className="lbl">Missing</span> <SkillChips items={match.missing_preferred} kind="neutral" /></p>
        </div>
      </div>
      {match.top_shared_terms.length > 0 && (<><h4>Shared terms in the text</h4><SkillChips items={match.top_shared_terms} kind="neutral" /></>)}
      <p className="disclaimer">{match.disclaimer}</p>
    </div>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <header><h3>{title}</h3><button className="btn btn-ghost" onClick={onClose} aria-label="Close dialog">&times;</button></header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export function SyntheticBanner({ text }: { text?: string }) {
  return (
    <div className="banner" role="note">
      <strong>Synthetic demo data.</strong> {text ?? "All jobs, companies and candidates are fictional. Scores are heuristic fit indicators, not probabilities of being hired."}
    </div>
  );
}

export function Loading({ what = "Loading" }: { what?: string }) {
  return <div className="loading" role="status" aria-live="polite"><span className="spinner" aria-hidden="true" />{what}&hellip;</div>;
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error-box" role="alert">
      <p>{message}</p>
      {onRetry && <button className="btn" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

export const StatusLabel = ({ status }: { status: string }) => <span className={`status status-${status}`}>{titleCase(status)}</span>;
