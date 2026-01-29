import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RuleEditor from "../pages/RuleEditor";
import { MemoryRouter } from "react-router-dom";
import { ruleAPI } from "../lib/api";

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("@monaco-editor/react", () => (props) => (
  <textarea
    data-testid="monaco-editor"
    value={props.value}
    onChange={(event) => props.onChange?.(event.target.value)}
  />
));

jest.mock("../lib/api");

describe("Rule Editor quality tools", () => {
  it("generates edge cases and exposes profiler/compliance actions", async () => {
    ruleAPI.getAll.mockResolvedValue({
      data: [
        {
          id: "rule-1",
          name: "VEL-001",
          rule_type: "velocity",
          status: "active",
          priority: 4,
          description: "Velocity check",
          conditions: [{ field: "tx_count", operator: ">", value: 8 }],
          actions: [{ type: "flag", severity: "medium" }],
          created_at: new Date().toISOString(),
        },
      ],
    });

    render(
      <MemoryRouter>
        <RuleEditor />
      </MemoryRouter>
    );

    await screen.findByTestId("rule-rule-1");

    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: /quality/i }));

    const generateBtn = await screen.findByTestId("generate-edge-cases-btn");
    await user.click(generateBtn);

    expect(await screen.findByText(/boundary case|Missing baseline history/i)).toBeInTheDocument();

    expect(screen.getByTestId("run-profiler-btn")).toBeInTheDocument();
    expect(screen.getByTestId("export-compliance-btn")).toBeInTheDocument();
  });
});
