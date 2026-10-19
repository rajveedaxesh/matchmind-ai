import { formatSalary, formatYears, parseList, rankingReason, scoreTone, sortedContributions, titleCase } from "../lib/format";
import { makeMatch } from "./fixtures";

describe("format helpers", () => {
  it("maps scores to tones at the band edges", () => {
    expect([100, 75, 74.9, 55, 35, 34.9, 0].map(scoreTone)).toEqual(["strong", "strong", "good", "good", "fair", "low", "low"]);
  });
  it("parses comma/newline lists, trimming and de-duplicating case-insensitively", () => {
    expect(parseList(" Python, sql ,\nPYTHON,  , Docker  Compose ")).toEqual(["Python", "sql", "Docker Compose"]);
    expect(parseList("")).toEqual([]);
  });
  it("formats salary and years, handling missing values", () => {
    expect(formatSalary({ salary_min: 80000, salary_max: 100000 })).toBe("$80k - $100k");
    expect(formatSalary({ salary_min: null, salary_max: null })).toBeNull();
    expect(formatYears({ min_years: 2, max_years: null })).toBe("2+ yrs");
    expect(formatYears({ min_years: null, max_years: null })).toBeNull();
  });
  it("title-cases enum values", () => { expect(titleCase("full-time")).toBe("Full Time"); });
  it("sorts only applicable components by contribution", () => {
    const sorted = sortedContributions(makeMatch());
    expect(sorted.map((c) => c.key)).toEqual(["required_skills", "text_similarity", "role_alignment", "preferred_skills"]);
  });
});

describe("rankingReason", () => {
  it("explains the lead using real contribution differences", () => {
    const upper = makeMatch(88);
    const lower = makeMatch(70);
    lower.components.required_skills = { ...lower.components.required_skills, contribution: 20 };
    const text = rankingReason(upper, lower);
    expect(text).toContain("by 18.0 points");
    expect(text).toContain("required skills");
  });
  it("handles ties and the last item", () => {
    expect(rankingReason(makeMatch(70), makeMatch(70))).toMatch(/Tied/);
    expect(rankingReason(makeMatch(70), null)).toMatch(/Last candidate/);
  });
});
