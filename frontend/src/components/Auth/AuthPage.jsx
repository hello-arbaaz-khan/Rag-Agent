import { useLocation, useNavigate } from "react-router-dom";
import LoginPage from "./LoginPage";
import SignupPage from "./SignupPage";
import VerifyOtpPage from "./VerifyOtpPage";
import ForgotPasswordPage from "./ForgotPasswordPage";
import ResetPasswordPage from "./ResetPasswordPage";
import { AUTH_SCREEN_PATHS } from "../../router/paths";

// Each auth screen now has its own URL (/login, /signup, /verify-otp,
// /forgot-password, /reset-password). The child pages still call
// onNavigate("verify-otp", { email }), so this adapter turns that into a
// router navigation and carries the email along.
//
// The email is also kept in sessionStorage so a refresh on /verify-otp or
// /reset-password doesn't lose it; it clears when the tab closes.
const EMAIL_KEY = "documind_auth_email";

const readStoredEmail = () => {
  try {
    return sessionStorage.getItem(EMAIL_KEY) || undefined;
  } catch {
    return undefined;
  }
};

const storeEmail = (email) => {
  try {
    if (email) sessionStorage.setItem(EMAIL_KEY, email);
  } catch {
    // ignore storage errors (e.g. private browsing)
  }
};

const AuthPage = ({ screen = "login" }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const email = location.state?.email ?? readStoredEmail();

  const handleNavigate = (nextScreen, nextParams = {}) => {
    storeEmail(nextParams.email);
    navigate(AUTH_SCREEN_PATHS[nextScreen] || AUTH_SCREEN_PATHS.login, {
      state: { ...nextParams, from: location.state?.from }
    });
  };

  switch (screen) {
    case "signup":
      return <SignupPage onNavigate={handleNavigate} />;
    case "verify-otp":
      return <VerifyOtpPage onNavigate={handleNavigate} email={email} />;
    case "forgot-password":
      return <ForgotPasswordPage onNavigate={handleNavigate} />;
    case "reset-password":
      return <ResetPasswordPage onNavigate={handleNavigate} email={email} />;
    case "login":
    default:
      return <LoginPage onNavigate={handleNavigate} />;
  }
};

export default AuthPage;