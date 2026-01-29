import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Layout from "../components/Layout";
import { battleAPI, ruleAPI, evidenceAPI } from "../lib/api";
import { MemoryRouter } from "react-router-dom";

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("../contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { role: "admin", name: "Demo User" },
    logout: jest.fn(),
    isDemoUser: false,
    switchRole: jest.fn(),
    roleDefinitions: {
      admin: { label: "Administrator" },
      analyst: { label: "Fraud Analyst" },
      engineer: { label: "Security Engineer" },
      compliance: { label: "Compliance Officer" },
    },
  }),
  ROLE_DEFINITIONS: {
    admin: { label: "Administrator" },
    analyst: { label: "Fraud Analyst" },
    engineer: { label: "Security Engineer" },
    compliance: { label: "Compliance Officer" },
  },
}));

jest.mock("../contexts/AlertContext", () => ({
  useAlerts: () => ({
    unreadCount: 0,
    criticalCount: 0,
    currentPreset: "moderate",
  }),
}));

jest.mock("../components/AlertPanels", () => ({
  AlertHistoryPanel: () => null,
  ThresholdConfigPanel: () => null,
}));

jest.mock("../components/CollaborationIndicator", () => () => null);
jest.mock("../components/KeyboardShortcutsOverlay", () => () => null);
jest.mock("../components/HelpCenter", () => () => null);
jest.mock("../components/OnboardingWizard", () => () => null);
jest.mock("../components/FloatingHelp", () => () => null);

jest.mock("../lib/api");

describe("Layout global search", () => {
  it("shows indexed results for battles, rules, and evidence", async () => {
    battleAPI.getAll.mockResolvedValue({ data: [{ id: "b-1", scenario_name: "Red Burst", status: "completed" }] });
    ruleAPI.getAll.mockResolvedValue({ data: [{ id: "r-1", name: "VEL-001", rule_type: "velocity" }] });
    evidenceAPI.getAll.mockResolvedValue({ data: [{ id: "e-1", name: "Pack Alpha" }] });

    render(
      <MemoryRouter initialEntries={["/war-room"]}>
        <Layout />
      </MemoryRouter>
    );

    const searchInput = screen.getByTestId("global-search");
    fireEvent.focus(searchInput);
    await waitFor(() => expect(screen.getByTestId("layout-container")).toBeInTheDocument());
    await waitFor(() => expect(battleAPI.getAll).toHaveBeenCalled());
    fireEvent.change(searchInput, { target: { value: "Red" } });
    await waitFor(() => expect(screen.getByText("Red Burst")).toBeInTheDocument());

    fireEvent.change(searchInput, { target: { value: "VEL" } });
    await waitFor(() => expect(screen.getByText("VEL-001")).toBeInTheDocument());

    fireEvent.change(searchInput, { target: { value: "Pack" } });
    await waitFor(() => expect(screen.getByText("Pack Alpha")).toBeInTheDocument());
  });
});
