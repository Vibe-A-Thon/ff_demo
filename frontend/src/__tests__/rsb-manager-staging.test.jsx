import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import RSBManager from "../pages/RSBManager";
import { rsbAPI } from "../lib/api";

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("react-force-graph-2d", () => () => <div data-testid="force-graph" />);

jest.mock("../lib/api");

const createDataTransfer = (data) => ({
  data: data,
  getData: (key) => data[key],
  setData: () => {},
  effectAllowed: "move",
  dropEffect: "move",
});

describe("RSB Manager staging queue", () => {
  it("allows staging packages and shows deploy action", async () => {
    rsbAPI.getAll.mockResolvedValue({
      data: [
        {
          id: "pkg-1",
          name: "Core Fraud Pack",
          version: "2.1.0",
          status: "pending",
          manifest: { rules: 3 },
          compliance_badges: ["SOX"],
          rules: ["R-001"],
        },
      ],
    });

    render(<RSBManager />);

    const packageCard = await screen.findByTestId("package-pkg-1");
    fireEvent.click(packageCard);

    const dropzone = await screen.findByTestId("staging-dropzone");
    fireEvent.drop(dropzone, {
      dataTransfer: createDataTransfer({ "application/json": JSON.stringify({ id: "pkg-1", name: "Core Fraud Pack" }) }),
    });

    expect(await screen.findByTestId("remove-staged-pkg-1")).toBeInTheDocument();
    expect(screen.getByTestId("deploy-staged-btn")).toBeInTheDocument();
  });
});
