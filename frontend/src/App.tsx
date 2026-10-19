import { useEffect, useState } from "react";
import { Applications } from "./pages/Applications";
import { Evaluation } from "./pages/Evaluation";
import { Jobs } from "./pages/Jobs";
import { Overview } from "./pages/Overview";
import { ProfilePage } from "./pages/Profile";
import { Recruiter } from "./pages/Recruiter";

export const ROUTES = [
  { id: "overview", label: "Overview", group: "Job seeker" },
  { id: "jobs", label: "Job discovery", group: "Job seeker" },
  { id: "applications", label: "Saved & applied", group: "Job seeker" },
  { id: "profile", label: "My profile", group: "Job seeker" },
  { id: "recruiter", label: "Candidate matching", group: "Recruiter" },
  { id: "evaluation", label: "Model evaluation", group: "Model" },
] as const;

const fromHash = () => {
  const id = window.location.hash.replace(/^#\/?/, "");
  return ROUTES.some((r) => r.id === id) ? id : "overview";
};

export default function App() {
  const [route, setRoute] = useState(fromHash());
  useEffect(() => {
    const onHash = () => setRoute(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const go = (id: string) => { window.location.hash = `/${id}`; };

  let groupShown = "";
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-mark" aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 32 32" fill="none" stroke="#fff" strokeWidth="3"><circle cx="12" cy="16" r="6" /><circle cx="20" cy="16" r="6" /></svg>
          </span>
          MatchMind AI
        </div>
        <nav className="nav" aria-label="Main">
          {ROUTES.map((r) => {
            const header = r.group !== groupShown ? <div className="nav-group" key={`g-${r.group}`}>{r.group}</div> : null;
            groupShown = r.group;
            return (
              <span key={r.id} style={{ display: "contents" }}>
                {header}
                <a href={`#/${r.id}`} aria-current={route === r.id ? "page" : undefined}>{r.label}</a>
              </span>
            );
          })}
        </nav>
        <div className="sidebar-foot">Fictional demo data. Scores are fit indicators, not hiring probabilities.</div>
      </aside>
      <main className="main" id="main">
        {route === "overview" && <Overview go={go} />}
        {route === "jobs" && <Jobs />}
        {route === "applications" && <Applications />}
        {route === "profile" && <ProfilePage />}
        {route === "recruiter" && <Recruiter />}
        {route === "evaluation" && <Evaluation />}
      </main>
    </div>
  );
}
