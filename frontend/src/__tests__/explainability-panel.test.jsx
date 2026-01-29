import React from "react";
import { render, screen } from "@testing-library/react";
import ExplainabilityPanel from "../components/ExplainabilityPanel";

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

describe("ExplainabilityPanel", () => {
  it("renders contradictions and learning context", () => {
    render(
      <ExplainabilityPanel
        open={true}
        onOpenChange={jest.fn()}
        payload={{
          title: "Test Explainability",
          summary: "Summary",
          confidence: 0.9,
          triggeredRules: ["R-TEST-1"],
          evidence: ["Evidence A"],
          similarCases: ["Case-001"],
          contradictions: [
            {
              id: "c-1",
              title: "Rule conflict",
              detail: "Conflicting rules detected",
              severity: "high",
            },
          ],
          learningContext: {
            summary: "Learning summary",
            impact: "Impact statement",
            nextActions: ["Action 1"],
          },
          audienceViews: {
            regulator: "Regulator view",
            customer: "Customer view",
            investigator: "Investigator view",
          },
        }}
      />
    );

    expect(screen.getByTestId("explain-panel")).toBeInTheDocument();
    expect(screen.getByText("Contradiction Detection")).toBeInTheDocument();
    expect(screen.getByText("Learning Context")).toBeInTheDocument();
    expect(screen.getByTestId("explain-export-btn")).toBeInTheDocument();
  });
});
