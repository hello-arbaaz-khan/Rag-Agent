import { useState } from "react";
import LoginPage from "./LoginPage";
import SignupPage from "./SignupPage";
import VerifyOtpPage from "./VerifyOtpPage";
import ForgotPasswordPage from "./ForgotPasswordPage";
import ResetPasswordPage from "./ResetPasswordPage";

// Simple state-based screen switcher — this repo has no react-router
// installed, so this mirrors the same pattern App.jsx already uses for
// switching between "chat" and "search" views.
//
// Persisted to sessionStorage so a refresh mid-flow (e.g. sitting on the
// "verify OTP" screen) doesn't silently drop you back to the login page —
// it clears itself once you log in/out or close the tab.
const STORAGE_KEY = "documind_auth_screen";

const loadInitialState = () => {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { screen: "login", params: {} };
    const parsed = JSON.parse(raw);
    if (!parsed?.screen) return { screen: "login", params: {} };
    return parsed;
  } catch {
    return { screen: "login", params: {} };
  }
};

const AuthPage = () => {
  const initial = loadInitialState();
  const [screen, setScreen] = useState(initial.screen);
  const [params, setParams] = useState(initial.params);

  const navigate = (nextScreen, nextParams = {}) => {
    setParams(nextParams);
    setScreen(nextScreen);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ screen: nextScreen, params: nextParams }));
    } catch {
      // ignore storage errors (e.g. private browsing)
    }
  };

  switch (screen) {
    case "signup":
      return <SignupPage onNavigate={navigate} />;
    case "verify-otp":
      return <VerifyOtpPage onNavigate={navigate} email={params.email} />;
    case "forgot-password":
      return <ForgotPasswordPage onNavigate={navigate} />;
    case "reset-password":
      return <ResetPasswordPage onNavigate={navigate} email={params.email} />;
    case "login":
    default:
      return <LoginPage onNavigate={navigate} />;
  }
};

export default AuthPage;