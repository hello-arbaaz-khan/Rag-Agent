import { Suspense } from "react";
import App from "./App.jsx";
import AuthPage from "./components/Auth/AuthPage.jsx";
import { useAuth } from "./context/AuthContext";

const Root = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Suspense fallback={<div className="h-screen flex items-center justify-center bg-brand-bg" />}>
      {isAuthenticated ? <App /> : <AuthPage />}
    </Suspense>
  );
};

export default Root;