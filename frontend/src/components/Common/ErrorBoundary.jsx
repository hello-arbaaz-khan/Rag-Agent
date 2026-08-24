import { Component } from "react";
import { AlertCircle } from "lucide-react";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen flex-col items-center justify-center bg-white p-6 text-center dark:bg-brand-bg">
          <AlertCircle className="mb-4 h-12 w-12 text-red-500" />
          <h1 className="mb-2 text-2xl font-bold text-slate-900 dark:text-white">
            Something went wrong
          </h1>
          <p className="mb-6 text-slate-600 dark:text-slate-400">
            {this.state.error?.message || "An unexpected error occurred"}
          </p>
          <details className="mb-6 rounded bg-slate-100 p-4 text-left dark:bg-slate-900">
            <summary className="cursor-pointer font-mono text-sm text-slate-600 dark:text-slate-400">
              Error details
            </summary>
            <pre className="mt-2 overflow-auto whitespace-pre-wrap break-words text-xs">
              {this.state.error?.stack}
            </pre>
          </details>
          <button
            onClick={() => window.location.href = "/"}
            className="rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-500"
          >
            Refresh page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
