"use client";

import { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="rounded-lg border border-unfavorable-bg bg-unfavorable-bg p-6 text-center">
          <h3 className="text-sm font-medium text-unfavorable-dark mb-1">
            Something went wrong
          </h3>
          <p className="text-xs text-unfavorable">
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
