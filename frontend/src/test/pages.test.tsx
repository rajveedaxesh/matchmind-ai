import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { Evaluation } from "../pages/Evaluation";
import { Jobs } from "../pages/Jobs";
import { ProfilePage } from "../pages/Profile";
import { Recruiter } from "../pages/Recruiter";
import { evaluation, makeJob, makeMatch, mockFetch, profile, recruiterResponse } from "./fixtures";

afterEach(() => vi.unstubAllGlobals());

const jobsPayload = (items = [makeJob(1), makeJob(2, { title: "Second Role" })]) => ({ items, total: items.length, limit: 10, offset: 0 });

describe("Jobs page", () => {
  it("lists jobs with the user's match score and sends filters to the API", async () => {
    const calls = mockFetch((url) => {
      if (url.pathname === "/api/jobs") return { body: jobsPayload() };
      if (url.pathname === "/api/recommendations") return { body: { items: [{ rank: 1, job: makeJob(1), match: makeMatch(91) }] } };
    });
    const user = userEvent.setup();
    render(<Jobs />);
    expect(await screen.findByText("Job 1")).toBeInTheDocument();
    expect(await screen.findByRole("img", { name: /Match score 91/ })).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Work mode"), "remote");
    await waitFor(() => expect(calls.some((c) => c.url.pathname === "/api/jobs" && c.url.searchParams.get("work_mode") === "remote")).toBe(true));
  });

  it("shows an empty state when no job matches", async () => {
    mockFetch((url) => (url.pathname === "/api/jobs" ? { body: jobsPayload([]) } : { body: { items: [] } }));
    render(<Jobs />);
    expect(await screen.findByText(/No jobs match these filters/)).toBeInTheDocument();
  });

  it("shows an error with retry when the API fails", async () => {
    mockFetch((url) => (url.pathname === "/api/jobs" ? { status: 500, body: { detail: "boom" } } : { body: { items: [] } }));
    render(<Jobs />);
    expect(await screen.findByRole("alert")).toHaveTextContent("boom");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("saves a job via the status menu (PUT) and rolls back on failure", async () => {
    let fail = false;
    const calls = mockFetch((url, init) => {
      if (url.pathname === "/api/jobs") return { body: jobsPayload([makeJob(1)]) };
      if (url.pathname === "/api/recommendations") return { body: { items: [] } };
      if (url.pathname === "/api/applications/1" && init?.method === "PUT") return fail ? { status: 404, body: { detail: "Job 1 not found" } } : { body: {} };
    });
    const user = userEvent.setup();
    render(<Jobs />);
    const select = await screen.findByLabelText("Application status for Job 1");
    await user.selectOptions(select, "applied");
    await waitFor(() => expect(calls.some((c) => c.init?.method === "PUT")).toBe(true));
    const put = calls.find((c) => c.init?.method === "PUT")!;
    expect(JSON.parse(String(put.init!.body))).toMatchObject({ status: "applied" });
    fail = true;
    await user.selectOptions(await screen.findByLabelText("Application status for Job 1"), "offer");
    expect(await screen.findByText("Job 1 not found")).toBeInTheDocument();
  });

  it("opens a match explanation dialog", async () => {
    mockFetch((url) => {
      if (url.pathname === "/api/jobs") return { body: jobsPayload([makeJob(1)]) };
      if (url.pathname === "/api/recommendations") return { body: { items: [{ rank: 1, job: makeJob(1), match: makeMatch(77) }] } };
    });
    const user = userEvent.setup();
    render(<Jobs />);
    await user.click(await screen.findByRole("button", { name: "Why this match?" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("Why this score")).toBeInTheDocument();
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  });
});

describe("Profile page", () => {
  it("loads the profile, saves edits as parsed lists, and shows the new completeness", async () => {
    const calls = mockFetch((url, init) => {
      if (url.pathname === "/api/profile" && init?.method === "PUT") return { body: { ...profile, completeness: { percent: 100, missing: [] } } };
      if (url.pathname === "/api/profile") return { body: profile };
    });
    const user = userEvent.setup();
    render(<ProfilePage />);
    const skills = await screen.findByLabelText(/^Skills/);
    expect(skills).toHaveValue("Python, SQL");
    await user.clear(skills);
    await user.type(skills, "Python, sql, Docker, python");
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(await screen.findByText(/Profile saved/)).toBeInTheDocument();
    const body = JSON.parse(String(calls.find((c) => c.init?.method === "PUT")!.init!.body));
    expect(body.skills).toEqual(["Python", "sql", "Docker"]);
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("blocks non-numeric experience client-side without calling the API", async () => {
    const calls = mockFetch((url) => (url.pathname === "/api/profile" ? { body: profile } : undefined));
    const user = userEvent.setup();
    render(<ProfilePage />);
    const years = await screen.findByLabelText(/Years of experience/);
    await user.clear(years);
    await user.type(years, "lots");
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect(await screen.findByText(/Enter a number/)).toBeInTheDocument();
    expect(calls.filter((c) => c.init?.method === "PUT")).toHaveLength(0);
  });

  it("displays server-side validation errors next to the field", async () => {
    mockFetch((url, init) => {
      if (url.pathname === "/api/profile" && init?.method === "PUT") return { status: 422, body: { detail: [{ loc: ["body", "headline"], msg: "String should have at least 2 characters" }] } };
      if (url.pathname === "/api/profile") return { body: profile };
    });
    const user = userEvent.setup();
    render(<ProfilePage />);
    const headline = await screen.findByLabelText(/Headline/);
    await user.clear(headline);
    await user.type(headline, "x");
    await user.click(screen.getByRole("button", { name: "Save profile" }));
    expect((await screen.findAllByText(/at least 2 characters/)).length).toBeGreaterThan(0);
    expect(headline).toHaveAttribute("aria-invalid", "true");
  });
});

describe("Recruiter page", () => {
  const handler = (url: URL, init?: RequestInit) => {
    if (url.pathname === "/api/jobs") return { body: jobsPayload() };
    if (url.pathname === "/api/recruiter/match" && init?.method === "POST") return { body: recruiterResponse };
  };

  it("ranks candidates for a selected job and explains the order", async () => {
    const calls = mockFetch(handler);
    const user = userEvent.setup();
    render(<Recruiter />);
    const run = screen.getByRole("button", { name: "Rank candidates" });
    expect(run).toBeDisabled();
    await user.selectOptions(await screen.findByLabelText("Job"), "1");
    expect(run).toBeEnabled();
    await user.click(run);
    expect(await screen.findByText(/Avery Test/)).toBeInTheDocument();
    const cards = screen.getAllByRole("listitem");
    expect(cards[0]).toHaveTextContent("Avery Test");
    expect(cards[1]).toHaveTextContent("Blake Test");
    expect(within(cards[1]).getByText("airflow")).toHaveClass("chip-missing");
    expect(within(cards[0]).getByText(/Why this rank/).parentElement).toHaveTextContent(/Ahead of the next candidate by 27\.0 points/);
    expect(JSON.parse(String(calls.find((c) => c.init?.method === "POST")!.init!.body))).toMatchObject({ job_id: 1, method: "hybrid" });
  });

  it("supports a custom description and the TF-IDF baseline toggle", async () => {
    const calls = mockFetch(handler);
    const user = userEvent.setup();
    render(<Recruiter />);
    await user.click(screen.getByRole("button", { name: "Enter a description" }));
    await user.click(screen.getByRole("button", { name: "TF-IDF baseline" }));
    const run = screen.getByRole("button", { name: "Rank candidates" });
    await user.type(screen.getByLabelText("Job title"), "ML Engineer");
    await user.type(screen.getByLabelText(/^Description/), "Short");
    expect(run).toBeDisabled(); // description shorter than 20 characters
    await user.type(screen.getByLabelText(/^Description/), " but now a long enough description.");
    await user.click(run);
    await screen.findByText(/Avery Test/);
    const body = JSON.parse(String(calls.find((c) => c.init?.method === "POST")!.init!.body));
    expect(body.method).toBe("tfidf");
    expect(body.job.title).toBe("ML Engineer");
  });

  it("shows the API's validation message when matching fails", async () => {
    mockFetch((url, init) => {
      if (url.pathname === "/api/jobs") return { body: jobsPayload() };
      if (init?.method === "POST") return { status: 404, body: { detail: "Job 1 not found" } };
    });
    const user = userEvent.setup();
    render(<Recruiter />);
    await user.selectOptions(await screen.findByLabelText("Job"), "1");
    await user.click(screen.getByRole("button", { name: "Rank candidates" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Job 1 not found");
  });
});

describe("Evaluation page", () => {
  it("renders real-looking metrics, labels data as synthetic and switches direction", async () => {
    mockFetch((url) => (url.pathname === "/api/evaluation" ? { body: evaluation } : undefined));
    const user = userEvent.setup();
    render(<Evaluation />);
    expect(await screen.findByText(/Synthetic demo data/)).toBeInTheDocument();
    expect(await screen.findByRole("columnheader", { name: "ndcg@5" })).toBeInTheDocument();
    expect(screen.getByText(/interval includes 0/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Job seeker/ }));
    expect(await screen.findByText(/interval excludes 0/)).toBeInTheDocument();
    expect(screen.getAllByText("TF-IDF baseline").length).toBeGreaterThan(0);
  });
});

describe("App shell", () => {
  it("navigates between pages via the hash router and marks the current page", async () => {
    mockFetch((url) => {
      if (url.pathname === "/api/evaluation") return { body: evaluation };
      if (url.pathname === "/api/meta") return { body: { counts: { jobs: 32, candidates: 18 }, data_notice: "FICTIONAL data", embedding_backend: "lsa", embedding_fallback_reason: null } };
      if (url.pathname === "/api/profile") return { body: profile };
      if (url.pathname === "/api/recommendations") return { body: { items: [], warnings: [] } };
      if (url.pathname === "/api/applications") return { body: { items: [], counts: {} } };
    });
    window.location.hash = "";
    render(<App />);
    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute("aria-current", "page");
    window.location.hash = "#/evaluation";
    await waitFor(() => expect(screen.getByRole("link", { name: "Model evaluation" })).toHaveAttribute("aria-current", "page"));
    expect(await screen.findByRole("heading", { name: "Model evaluation" })).toBeInTheDocument();
  });
});
