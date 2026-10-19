import { ApiError, api, parseErrorBody } from "../api";
import { mockFetch } from "./fixtures";

afterEach(() => vi.unstubAllGlobals());

describe("parseErrorBody", () => {
  it("uses string details", () => {
    const e = parseErrorBody(404, { detail: "Job 5 not found" });
    expect(e.message).toBe("Job 5 not found");
    expect(e.status).toBe(404);
  });
  it("maps 422 validation lists to per-field errors and strips the pydantic prefix", () => {
    const e = parseErrorBody(422, { detail: [
      { loc: ["body", "years_experience"], msg: "Input should be greater than or equal to 0" },
      { loc: ["body"], msg: "Value error, Protected attribute(s) ['age'] are not accepted" },
    ] });
    expect(e.fieldErrors.years_experience).toMatch(/greater than or equal/);
    expect(e.message).toContain("Protected attribute");
    expect(e.message).not.toContain("Value error");
  });
  it("falls back to a generic message", () => { expect(parseErrorBody(500, null).message).toBe("Request failed (500)"); });
});

describe("api client", () => {
  it("builds query strings and skips empty filters", async () => {
    const calls = mockFetch(() => ({ body: { items: [], total: 0, limit: 10, offset: 0 } }));
    await api.jobs({ q: "python", work_mode: "", location: undefined, limit: 10 });
    expect(calls[0].url.pathname).toBe("/api/jobs");
    expect(calls[0].url.searchParams.get("q")).toBe("python");
    expect(calls[0].url.searchParams.has("work_mode")).toBe(false);
    expect(calls[0].url.searchParams.get("limit")).toBe("10");
  });
  it("throws ApiError with the server's message", async () => {
    mockFetch(() => ({ status: 404, body: { detail: "Job 9 not found" } }));
    await expect(api.job(9)).rejects.toMatchObject({ name: "ApiError", message: "Job 9 not found", status: 404 });
  });
  it("reports an unreachable backend clearly", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("network"); }));
    await expect(api.meta()).rejects.toBeInstanceOf(ApiError);
    await expect(api.meta()).rejects.toThrow(/Cannot reach/);
  });
  it("handles 204 responses", async () => {
    mockFetch(() => ({ status: 204 }));
    await expect(api.removeApplication(1)).resolves.toBeUndefined();
  });
});
