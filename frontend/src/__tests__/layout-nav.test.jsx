import React from "react";
import { render, screen } from "@testing-library/react";
import Layout from "../components/Layout";
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

jest.mock("../lib/api");

jest.mock("../components/AlertPanels", () => ({
  AlertHistoryPanel: () => null,
  ThresholdConfigPanel: () => null,
}));

jest.mock("../components/CollaborationIndicator", () => () => null);
jest.mock("../components/KeyboardShortcutsOverlay", () => () => null);
jest.mock("../components/HelpCenter", () => () => null);
jest.mock("../components/OnboardingWizard", () => () => null);
jest.mock("../components/FloatingHelp", () => () => null);

describe("Layout navigation", () => {
  it("renders core navigation items", async () => {
    render(
      <MemoryRouter initialEntries={["/war-room"]}>
        <Layout />
      </MemoryRouter>
    );

    await screen.findByTestId("layout-container");

    expect(screen.getByTestId("nav-war-room")).toBeInTheDocument();
    expect(screen.getByTestId("nav-battle-replay")).toBeInTheDocument();
    expect(screen.getByTestId("nav-brain-surgery")).toBeInTheDocument();
    expect(screen.getByTestId("nav-metrics")).toBeInTheDocument();
    expect(screen.getByTestId("nav-rsb-manager")).toBeInTheDocument();
    expect(screen.getByTestId("nav-diff-viewer")).toBeInTheDocument();
    expect(screen.getByTestId("nav-evidence")).toBeInTheDocument();
    expect(screen.getByTestId("nav-rules")).toBeInTheDocument();
    expect(screen.getByTestId("nav-approvals")).toBeInTheDocument();
  });
});
