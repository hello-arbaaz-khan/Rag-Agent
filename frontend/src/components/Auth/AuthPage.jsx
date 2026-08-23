import { useState } from "react";
import LoginPage from "./LoginPage";
import SignupPage from "./SignupPage";
import VerifyOtpPage from "./VerifyOtpPage";
import ForgotPasswordPage from "./ForgotPasswordPage";
import ResetPasswordPage from "./ResetPasswordPage";

// Simple state-based screen switcher — this repo has no react-router
// installed, so this mirrors the same pattern App.jsx already uses for
// switching between "chat" and "search" views.
const AuthPage = () => {
  const [screen, setScreen] = useState("login");
  const [params, setParams] = useState({});

  const navigate = (nextScreen, nextParams = {}) => {
    setParams(nextParams);
    setScreen(nextScreen);
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