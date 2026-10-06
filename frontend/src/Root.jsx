import { Suspense } from "react";
import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import App from "./App.jsx";
import AuthPage from "./components/Auth/AuthPage.jsx";
import DriveCallbackPage from "./components/Drive/DriveCallbackPage.jsx";
import ErrorBoundary from "./components/Common/ErrorBoundary.jsx";
import { useAuth } from "./context/AuthContext";
import { AUTH_SCREEN_PATHS, PATHS } from "./router/paths";
import { ChatPage, DocumentsPage, NewChatPage, SearchPage, SettingsPage } from "./router/pages.jsx";

// Signed-in only. Unauthenticated visitors go to /login and are sent back
// to the page they asked for once they sign in.
const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to={PATHS.login} replace state={{ from: location }} />;
  }
  return <Outlet />;
};

// Signed-out only (login, signup, OTP, password reset).
const PublicOnlyRoute = () => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (isAuthenticated) {
    const from = location.state?.from;
    const target = from?.pathname ? `${from.pathname}${from.search || ""}` : PATHS.newChat;
    return <Navigate to={target} replace />;
  }
  return <Outlet />;
};

// "/" -> the new-chat screen. Also catches the old OAuth redirect shape
// ("/?drive_status=...") and forwards it to the callback route.
const IndexRedirect = () => {
  const { search } = useLocation();

  if (new URLSearchParams(search).has("drive_status")) {
    return <Navigate to={`${PATHS.driveCallback}${search}`} replace />;
  }
  return <Navigate to={PATHS.newChat} replace />;
};

const Root = () => (
  <ErrorBoundary>
    <Suspense fallback={<div className="h-screen flex items-center justify-center bg-brand-bg" />}>
      <Routes>
        <Route path="/" element={<IndexRedirect />} />

        {/* The Google Drive OAuth popup lands here (drive_service redirects to it). */}
        <Route path={PATHS.driveCallback} element={<DriveCallbackPage />} />

        <Route element={<PublicOnlyRoute />}>
          {Object.entries(AUTH_SCREEN_PATHS).map(([screen, path]) => (
            <Route key={screen} path={path} element={<AuthPage screen={screen} />} />
          ))}
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<App />}>
            <Route path={PATHS.newChat} element={<NewChatPage />} />
            <Route path="/chat/:documentId" element={<ChatPage />} />
            <Route path={PATHS.documents} element={<DocumentsPage />} />
            <Route path={PATHS.search} element={<SearchPage />} />
            <Route path={PATHS.settings} element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to={PATHS.newChat} replace />} />
      </Routes>
    </Suspense>
  </ErrorBoundary>
);

export default Root;