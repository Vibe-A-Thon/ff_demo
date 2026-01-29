import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Approvals from "../pages/Approvals";
import { approvalAPI, ruleAPI, rsbAPI } from "../lib/api";

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("../lib/api");

describe("Approvals emergency override", () => {
  it("opens override modal with justification controls", async () => {
    approvalAPI.getAll.mockResolvedValue({
      data: [
        {
          id: "app-1",
          status: "pending",
          resource_type: "rule",
          resource_id: "rule-1",
          action: "deploy",
          requestor_id: "dev@fraudforge",
          created_at: new Date().toISOString(),
          approvers: [],
        },
      ],
    });
    ruleAPI.getAll.mockResolvedValue({ data: [] });
    rsbAPI.getAll.mockResolvedValue({ data: [] });

    render(<Approvals />);

    await waitFor(() => expect(screen.getByText("Approval Queue")).toBeInTheDocument());
    const approvalItem = await screen.findByTestId("approval-app-1");
    fireEvent.click(approvalItem);

    const overrideBtn = await screen.findByTestId("emergency-override-btn");
    fireEvent.click(overrideBtn);

    expect(await screen.findByTestId("override-modal")).toBeInTheDocument();
    expect(screen.getByTestId("override-reason-input")).toBeInTheDocument();
    expect(screen.getByTestId("override-impact-select")).toBeInTheDocument();
  });
});
