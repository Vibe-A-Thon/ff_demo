import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import MetricsDashboard from "../pages/MetricsDashboard";
import { metricsAPI } from "../lib/api";

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("../lib/api");

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ families: [] }),
    })
  );
});

describe("Metrics Dashboard", () => {
  it("renders coverage heatmap and cost breakdown", async () => {
    metricsAPI.getDashboard.mockResolvedValue({
      data: {
        total_battles: 5,
        completed_battles: 4,
        running_battles: 1,
        avg_success_rate: 78,
        total_rules: 12,
        active_rules: 10,
        patterns_learned: 30,
        avg_time_to_immunity: 5.1,
        time_series: [
          { success_rate: 62, time_to_immunity: 8, patterns_learned: 8 },
          { success_rate: 78, time_to_immunity: 5, patterns_learned: 30 },
        ],
      },
    });
    render(<MetricsDashboard />);

    await waitFor(() => expect(screen.getByText("Metrics Dashboard")).toBeInTheDocument());

    expect(await screen.findByTestId("coverage-heatmap")).toBeInTheDocument();
    expect(screen.getByText(/Cost-Benefit Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Net Value/i)).toBeInTheDocument();
  });
});
