import React from "react";
import { render, screen } from "@testing-library/react";
import Login from "../pages/Login";
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
    login: jest.fn(),
    register: jest.fn(),
  }),
}));

describe("Login page", () => {
  it("renders core login UI", () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    expect(screen.getByTestId("login-page")).toBeInTheDocument();
    expect(screen.getByTestId("login-tab")).toBeInTheDocument();
    expect(screen.getByTestId("register-tab")).toBeInTheDocument();
    expect(screen.getByTestId("login-email-input")).toBeInTheDocument();
    expect(screen.getByTestId("login-password-input")).toBeInTheDocument();
    expect(screen.getByTestId("login-submit-btn")).toBeInTheDocument();
    expect(screen.getByTestId("demo-login-btn")).toBeInTheDocument();
  });
});
