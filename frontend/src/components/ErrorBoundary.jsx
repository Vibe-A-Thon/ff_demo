import React from "react";
import { Button } from "./ui/button";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("UI Error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-6" data-testid="error-boundary">
          <div className="max-w-md w-full rounded-lg border border-border bg-card p-6 text-center">
            <div className="mx-auto mb-3 h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-400">
              <span className="text-xl">!</span>
            </div>
            <h2 className="text-lg font-semibold text-red-400">Something went wrong</h2>
            <p className="text-sm text-muted-foreground mt-2">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <Button
              className="mt-4"
              onClick={() => window.location.reload()}
              data-testid="error-boundary-reload"
            >
              Reload Application
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
