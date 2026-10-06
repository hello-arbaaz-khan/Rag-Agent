import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAppContext } from "../context/AppContext";

// Every screen has its own URL, like claude.ai/new:
//   /new            start a new chat
//   /chat/:id       chat with one document
//   /documents      document library
//   /search         advanced search
//   /settings       Drive connection + password
//   /login ...      auth screens (signed-out only)
//   /drive/callback Google OAuth popup landing page
export const PATHS = {
  newChat: "/new",
  chat: (documentId) => `/chat/${documentId}`,
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

// Auth screen id (used by the existing auth pages' onNavigate) -> URL.
export const AUTH_SCREEN_PATHS = {
  login: PATHS.login,
  signup: PATHS.signup,
  "verify-otp": PATHS.verifyOtp,
  "forgot-password": PATHS.forgotPassword,
  "reset-password": PATHS.resetPassword
};

// Which sidebar item is highlighted for a given URL.
export const viewFromPath = (pathname) => {
  if (pathname.startsWith("/search")) return "search";
  if (pathname.startsWith("/documents")) return "documents";
  if (pathname.startsWith("/settings")) return "settings";
  return "chat";
};

// Keeps the old `onNavigate("chat" | "search" | "documents" | "settings")`
// contract the sidebar / top bar / quick-info components already use, but
// turns each call into a real browser navigation.
export const useViewNavigate = () => {
  const navigate = useNavigate();
  const { selectedDocumentId } = useAppContext();

  return useCallback(
    (view) => {
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
          navigate(selectedDocumentId ? PATHS.chat(selectedDocumentId) : PATHS.newChat);
      }
    },
    [navigate, selectedDocumentId]
  );
};