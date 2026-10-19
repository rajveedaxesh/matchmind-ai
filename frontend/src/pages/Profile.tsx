import { useEffect, useState, type FormEvent } from "react";
import { ApiError, api } from "../api";
import { ErrorBox, Loading } from "../components/ui";
import { parseList } from "../lib/format";
import { useAsync } from "../lib/useAsync";
import type { Profile as ProfileT, ProfileInput, WorkMode } from "../types";

const MODES: WorkMode[] = ["remote", "hybrid", "onsite"];

export function ProfilePage() {
  const profile = useAsync(() => api.profile(), []);
  const [form, setForm] = useState({
    display_name: "", headline: "", location: "", years: "", skills: "", summary: "",
    titles: "", locations: "", modes: [] as WorkMode[], relocate: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [saved, setSaved] = useState<ProfileT | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const p = profile.data;
    if (!p) return;
    setSaved(p);
    setForm({
      display_name: p.display_name ?? "", headline: p.headline, location: p.location ?? "",
      years: p.years_experience == null ? "" : String(p.years_experience), skills: p.skills.join(", "),
      summary: p.summary, titles: p.desired_titles.join(", "), locations: p.preferred_locations.join(", "),
      modes: p.preferred_work_modes, relocate: p.open_to_relocation,
    });
  }, [profile.data]);

  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setErrors({}); setMessage(null);
    const years = form.years.trim() === "" ? null : Number(form.years);
    if (years !== null && Number.isNaN(years)) { setErrors({ years_experience: "Enter a number, e.g. 4 or 2.5" }); return; }
    const body: ProfileInput = {
      display_name: form.display_name || null, headline: form.headline, location: form.location || null,
      years_experience: years, skills: parseList(form.skills), summary: form.summary,
      desired_titles: parseList(form.titles), preferred_locations: parseList(form.locations),
      preferred_work_modes: form.modes, open_to_relocation: form.relocate,
    };
    setSaving(true);
    try {
      const out = await api.saveProfile(body);
      setSaved(out);
      setMessage({ ok: true, text: "Profile saved. Recommendations now use your updated profile." });
    } catch (err) {
      if (err instanceof ApiError) { setErrors(err.fieldErrors); setMessage({ ok: false, text: err.message }); }
      else setMessage({ ok: false, text: "Something went wrong while saving." });
    } finally { setSaving(false); }
  }

  const toggleMode = (m: WorkMode) => set("modes", form.modes.includes(m) ? form.modes.filter((x) => x !== m) : [...form.modes, m]);
  const field = (k: string) => errors[k] ? <span className="field-error" role="alert">{errors[k]}</span> : null;

  if (profile.loading && !profile.data) return <Loading what="Loading profile" />;
  return (
    <>
      <div className="page-head"><div><h1>Your profile</h1><p>Only job-relevant information is collected. Protected characteristics (age, gender, ethnicity, photo, etc.) are rejected by the API and never used for ranking.</p></div></div>
      {profile.error && <ErrorBox message={profile.error} onRetry={profile.reload} />}
      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <form className="card stack" onSubmit={submit} aria-label="Profile form" noValidate>
          <div className="form-grid">
            <label>Display name (optional)<input value={form.display_name} onChange={(e) => set("display_name", e.target.value)} />{field("display_name")}</label>
            <label>Headline *<input value={form.headline} aria-invalid={!!errors.headline} onChange={(e) => set("headline", e.target.value)} />{field("headline")}</label>
            <label>Current location<input value={form.location} onChange={(e) => set("location", e.target.value)} />{field("location")}</label>
            <label>Years of experience<input inputMode="decimal" value={form.years} aria-invalid={!!errors.years_experience} onChange={(e) => set("years", e.target.value)} />{field("years_experience")}</label>
          </div>
          <label>Skills <span className="hint">comma-separated, e.g. Python, SQL, Docker</span>
            <textarea value={form.skills} onChange={(e) => set("skills", e.target.value)} />{field("skills")}</label>
          <label>Summary<textarea value={form.summary} onChange={(e) => set("summary", e.target.value)} />{field("summary")}</label>
          <div className="form-grid">
            <label>Desired job titles<input value={form.titles} onChange={(e) => set("titles", e.target.value)} />{field("desired_titles")}</label>
            <label>Preferred locations<input value={form.locations} onChange={(e) => set("locations", e.target.value)} />{field("preferred_locations")}</label>
          </div>
          <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
            <legend style={{ fontWeight: 600, fontSize: ".85rem", marginBottom: ".3rem" }}>Work mode preference</legend>
            <div className="row">
              {MODES.map((m) => <label key={m} className="check"><input type="checkbox" checked={form.modes.includes(m)} onChange={() => toggleMode(m)} />{m[0].toUpperCase() + m.slice(1)}</label>)}
              <label className="check"><input type="checkbox" checked={form.relocate} onChange={(e) => set("relocate", e.target.checked)} />Open to relocation</label>
            </div>{field("preferred_work_modes")}
          </fieldset>
          {message && <p role={message.ok ? "status" : "alert"} className={message.ok ? "" : "field-error"}>{message.text}</p>}
          <div><button className="btn btn-primary" disabled={saving} type="submit">{saving ? "Saving..." : "Save profile"}</button></div>
        </form>
        <aside className="card">
          <h3>Profile completeness</h3>
          <div className="progress" role="progressbar" aria-valuenow={saved?.completeness.percent ?? 0} aria-valuemin={0} aria-valuemax={100}><div style={{ width: `${saved?.completeness.percent ?? 0}%` }} /></div>
          <p style={{ marginTop: ".5rem" }}><strong>{saved?.completeness.percent ?? 0}%</strong> complete</p>
          {saved && saved.completeness.missing.length > 0 && <ul className="explain">{saved.completeness.missing.map((m) => <li key={m}>{m}</li>)}</ul>}
          <p className="muted" style={{ fontSize: ".82rem" }}>Missing fields are never guessed: unscored components are left out and the remaining weights are re-normalised.</p>
        </aside>
      </div>
    </>
  );
}
