import { Suspense } from "react";
import App from "./App.jsx";
import AuthPage from "./components/Auth/AuthPage.jsx";
import DriveCallbackPage from "./components/Drive/DriveCallbackPage.jsx";
import ErrorBoundary from "./components/Common/ErrorBoundary.jsx";
import { useAuth } from "./context/AuthContext";

// The Google Drive OAuth popup lands back here at "/?drive_status=..."
// (see drive_service's /callback redirect). Render the confirmation page
// standalone, before the normal auth-gated app, since this loads inside a
// short-lived popup window, not the main session.
const isDriveCallback = () => new URLSearchParams(window.location.search).has("drive_status");

const Root = () => {
  const { isAuthenticated } = useAuth();

  if (isDriveCallback()) {
    return <DriveCallbackPage />;
  }

  return (
    <ErrorBoundary>
      <Suspense fallback={<div className="h-screen flex items-center justify-center bg-brand-bg" />}>
        {isAuthenticated ? <App /> : <AuthPage />}
      </Suspense>
    </ErrorBoundary>
  );
};

export default Root;