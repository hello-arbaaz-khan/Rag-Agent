import { useEffect } from "react";
import { Navigate, useNavigate, useOutletContext, useParams } from "react-router-dom";
import ChatArea from "../components/Chat/ChatArea";
import DocumentsView from "../components/Documents/DocumentsView";
import AdvancedSearch from "../components/Search/AdvancedSearch";
import DriveConnection from "../components/Drive/DriveConnection";
import ChangePasswordPage from "../components/Auth/ChangePasswordPage";
import { useAppContext } from "../context/AppContext";
import { PATHS } from "./paths";

// Route pages rendered inside <App /> (the sidebar/top-bar layout).
// <App /> hands each page `openUpload` and `navigateToView` via outlet context.

export const NewChatPage = () => {
  const { openUpload, navigateToView } = useOutletContext();
  const { dispatch } = useAppContext();

  // /new means "no document selected".
  useEffect(() => {
    dispatch({ type: "SET_SELECTED_DOCUMENT", payload: null });
  }, [dispatch]);

  return <ChatArea onUploadClick={openUpload} onNavigate={navigateToView} />;
};

export const ChatPage = () => {
  const { openUpload, navigateToView } = useOutletContext();
  const { documentId } = useParams();
  const { documents, loadingDocuments, dispatch } = useAppContext();

  const id = Number(documentId);
  const validId = Number.isInteger(id) && id > 0;

  // The URL is the source of truth for which document is open.
  useEffect(() => {
    if (validId) dispatch({ type: "SET_SELECTED_DOCUMENT", payload: id });
  }, [dispatch, id, validId]);

  if (!validId) return <Navigate to={PATHS.newChat} replace />;
  if (loadingDocuments) return <div className="h-full" />;
  if (!documents.some((doc) => doc.id === id)) return <Navigate to={PATHS.newChat} replace />;

  return <ChatArea onUploadClick={openUpload} onNavigate={navigateToView} />;
};

export const DocumentsPage = () => {
  const { openUpload } = useOutletContext();
  const navigate = useNavigate();

  return (
    <DocumentsView
      onUploadClick={openUpload}
      onOpenInChat={(documentId) => navigate(documentId ? PATHS.chat(documentId) : PATHS.newChat)}
    />
  );
};

export const SearchPage = () => {
  const navigate = useNavigate();

  const handleOpenInChat = (result) => {
    if (result?.document_id) navigate(PATHS.chat(result.document_id));
  };

  return <AdvancedSearch onOpenInChat={handleOpenInChat} />;
};

export const SettingsPage = () => {
  const { navigateToView } = useOutletContext();

  return (
    <div className="flex min-h-full flex-col items-center gap-6 p-6">
      <DriveConnection />
      <ChangePasswordPage onDone={() => navigateToView("chat")} />
    </div>
  );
};