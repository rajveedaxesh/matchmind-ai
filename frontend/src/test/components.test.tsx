import { render, screen, within } from "@testing-library/react";
import { ComponentBars, MatchDetail, ScoreBadge, SkillChips } from "../components/ui";
import { makeMatch } from "./fixtures";

describe("ScoreBadge", () => {
  it("exposes the score to assistive tech", () => {
    render(<ScoreBadge score={82.4} label="Strong fit" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("Match score 82 out of 100, Strong fit");
  });
});

describe("SkillChips", () => {
  it("shows 'none' when empty and partial matches with their source skill", () => {
    const { rerender } = render(<SkillChips items={[]} kind="missing" />);
    expect(screen.getByText("none")).toBeInTheDocument();
    rerender(<SkillChips items={["python"]} kind="match" partial={[{ required: "kubernetes", via: "docker" }]} />);
    expect(screen.getByText("python")).toBeInTheDocument();
    expect(screen.getByText(/kubernetes/)).toHaveAttribute("title", expect.stringContaining("related to docker"));
  });
});

describe("ComponentBars", () => {
  it("lists every component and marks unscored ones instead of showing a fake zero", () => {
    render(<ComponentBars match={makeMatch()} />);
    const items = within(screen.getByLabelText("Component scores")).getAllByRole("listitem");
    expect(items).toHaveLength(6);
    expect(screen.getAllByText("not scored")).toHaveLength(2);
    expect(screen.getByText(/weight 40%/)).toBeInTheDocument();
  });
});

describe("MatchDetail", () => {
  it("shows explanations, missing skills and the not-a-probability disclaimer", () => {
    render(<MatchDetail match={makeMatch()} />);
    expect(screen.getByText("Matches 2 of 4 required skills.")).toBeInTheDocument();
    expect(screen.getByText("rust")).toHaveClass("chip-missing");
    expect(screen.getByText(/NOT probabilities of being hired/)).toBeInTheDocument();
    expect(screen.getByText(/Biggest contributor/)).toHaveTextContent("Required skills");
  });
});
