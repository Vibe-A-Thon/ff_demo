import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AgentTaskQueue from "../pages/AgentTaskQueue";

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
    user: { id: "user-1", email: "demo@example.com" },
  }),
}));

const mockAgentAPI = {
  listTasks: jest.fn(),
  listRequests: jest.fn(),
  executeTask: jest.fn(),
  routeTasks: jest.fn(),
  orchestrate: jest.fn(),
  listArtifacts: jest.fn(),
  getLineage: jest.fn(),
  completeTask: jest.fn(),
  respondRequest: jest.fn(),
};

const mockTeamAPI = {
  getAll: jest.fn(),
};

jest.mock("../lib/api", () => ({
  agentAPI: mockAgentAPI,
  teamAPI: mockTeamAPI,
}));

describe("AgentTaskQueue", () => {
  beforeEach(() => {
    mockTeamAPI.getAll.mockResolvedValue({
      data: [{ team_id: "red", internal_name: "Red Team" }],
    });
    mockAgentAPI.listTasks.mockResolvedValue({
      data: [
        {
          task_id: "task-1",
          team_id: "red",
          run_id: "ops",
          task_type: "status_check",
          status: "pending",
        },
      ],
    });
    mockAgentAPI.listRequests.mockResolvedValue({ data: [] });
    mockAgentAPI.executeTask.mockResolvedValue({ data: { status: "success", outputs: [] } });
    mockAgentAPI.routeTasks.mockResolvedValue({ data: { tasks: [] } });
    mockAgentAPI.orchestrate.mockResolvedValue({ data: { tasks: [] } });
  });

  it("routes tasks and orchestrates teams", async () => {
    render(
      <MemoryRouter>
        <AgentTaskQueue />
      </MemoryRouter>
    );

    await screen.findByTestId("agent-queue-tabs");

    fireEvent.change(screen.getByTestId("route-objective"), {
      target: { value: "Test objective" },
    });
    fireEvent.click(screen.getByTestId("route-submit"));

    await waitFor(() => {
      expect(mockAgentAPI.routeTasks).toHaveBeenCalled();
    });

    fireEvent.change(screen.getByTestId("orchestrate-objective"), {
      target: { value: "Cross-team objective" },
    });
    fireEvent.click(screen.getByTestId("orchestrate-submit"));

    await waitFor(() => {
      expect(mockAgentAPI.orchestrate).toHaveBeenCalled();
    });
  });

  it("executes a task", async () => {
    render(
      <MemoryRouter>
        <AgentTaskQueue />
      </MemoryRouter>
    );

    const executeButton = await screen.findByTestId("agent-task-execute-task-1");
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockAgentAPI.executeTask).toHaveBeenCalledWith("task-1");
    });
  });
});
