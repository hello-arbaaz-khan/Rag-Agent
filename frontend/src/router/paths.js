
import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

export const PATHS = {
  newChat: "/new",
  chat: (conversationId) => `/chat/${conversationId}`,
  documents: "/documents",
  search: "/search",
  settings: "/settings",
  login: "/login",
  signup: "/signup",
  verifyOtp: "/verify-otp",
  forgotPassword: "/forgot-password",
  resetPassword: "/reset-password",
  driveCallback: "/drive/callback"
};

export const AUTH_SCREEN_PATHS = {
  login: PATHS.login,
  signup: PATHS.signup,
  "verify-otp": PATHS.verifyOtp,
  "forgot-password": PATHS.forgotPassword,
  "reset-password": PATHS.resetPassword
};

export const viewFromPath = (pathname) => {
  if (pathname.startsWith("/search")) return "search";
  if (pathname.startsWith("/documents")) return "documents";
  if (pathname.startsWith("/settings")) return "settings";
  return "chat";
};

export const useViewNavigate = () => {
  const navigate = useNavigate();

  return useCallback((view) => {
    switch (view) {
      case "search":
        navigate(PATHS.search);
        break;
      case "documents":
        navigate(PATHS.documents);
        break;
      case "settings":
        navigate(PATHS.settings);
        break;
      case "chat":
      default:
        navigate(PATHS.newChat);
    }
  }, [navigate]);
};