import type { Match, ComponentScore, Job } from "../types";

export const titleCase = (s: string) => s.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export function scoreTone(score: number): "strong" | "good" | "fair" | "low" {
  if (score >= 75) return "strong";
  if (score >= 55) return "good";
  if (score >= 35) return "fair";
  return "low";
}

export function parseList(text: string): string[] {
  const seen = new Map<string, string>();
  for (const part of text.split(/[,\n]/)) {
    const v = part.trim().replace(/\s+/g, " ");
    if (v && !seen.has(v.toLowerCase())) seen.set(v.toLowerCase(), v);
  }
  return [...seen.values()];
}

export function formatSalary(job: Pick<Job, "salary_min" | "salary_max">): string | null {
  const { salary_min: lo, salary_max: hi } = job;
  const k = (n: number) => `$${Math.round(n / 1000)}k`;
  if (lo && hi) return `${k(lo)} - ${k(hi)}`;
  if (lo) return `from ${k(lo)}`;
  if (hi) return `up to ${k(hi)}`;
  return null;
}

export function formatYears(job: Pick<Job, "min_years" | "max_years">): string | null {
  const { min_years: lo, max_years: hi } = job;
  if (lo != null && hi != null) return `${lo}-${hi} yrs`;
  if (lo != null) return `${lo}+ yrs`;
  if (hi != null) return `up to ${hi} yrs`;
  return null;
}

/** Components that contributed to the score, sorted by points contributed (largest first). */
export function sortedContributions(match: Match): ComponentScore[] {
  return Object.values(match.components)
    .filter((c) => c.applicable)
    .sort((a, b) => b.contribution - a.contribution);
}

/**
 * Explain, from real component scores, why `upper` is ranked above `lower`.
 * Uses the difference in points contributed per component, so the reasons always add up.
 */
export function rankingReason(upper: Match, lower: Match | null): string {
  if (!lower) return "Last candidate in this list.";
  const diff = upper.score - lower.score;
  if (Math.abs(diff) < 0.05) return "Tied with the next candidate; ordered by required-skill coverage, then by ID.";
  const deltas = Object.keys(upper.components)
    .map((k) => ({ label: upper.components[k].label, delta: upper.components[k].contribution - (lower.components[k]?.contribution ?? 0) }))
    .filter((d) => Math.abs(d.delta) >= 0.05)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  const ahead = deltas.filter((d) => d.delta > 0).slice(0, 2);
  const behind = deltas.filter((d) => d.delta < 0).slice(0, 1);
  const parts = ahead.map((d) => `${d.label.toLowerCase()} (+${d.delta.toFixed(1)})`).join(" and ");
  let text = `Ahead of the next candidate by ${diff.toFixed(1)} points`;
  if (parts) text += `, mainly on ${parts}`;
  if (behind.length) text += `; slightly behind on ${behind[0].label.toLowerCase()} (${behind[0].delta.toFixed(1)})`;
  return text + ".";
}

export function fmt(n: number, digits = 3) { return n.toFixed(digits); }
