
import { useNavigate, useOutletContext, useParams, Navigate } from "react-router-dom";
import ChatArea from "../components/Chat/ChatArea";
import DocumentsView from "../components/Documents/DocumentsView";
import AdvancedSearch from "../components/Search/AdvancedSearch";
import DriveConnection from "../components/Drive/DriveConnection";
import ChangePasswordPage from "../components/Auth/ChangePasswordPage";
import { PATHS } from "./paths";

export const NewChatPage = () => {
  const { openUpload, navigateToView } = useOutletContext();

  return (
    <ChatArea
      conversationId={null}
      onUploadClick={openUpload}
      onNavigate={navigateToView}
    />
  );
};

export const ChatPage = () => {
  const { openUpload, navigateToView } = useOutletContext();
  const { conversationId } = useParams();
  const id = Number(conversationId);

  if (!Number.isInteger(id) || id < 1) {
    return <Navigate to={PATHS.newChat} replace />;
  }

  return (
    <ChatArea
      key={id}
      conversationId={id}
      onUploadClick={openUpload}
      onNavigate={navigateToView}
    />
  );
};

export const DocumentsPage = () => {
  const { openUpload } = useOutletContext();
  const navigate = useNavigate();

  return (
    <DocumentsView
      onUploadClick={openUpload}
      onOpenInChat={() => navigate(PATHS.newChat)}
    />
  );
};

export const SearchPage = () => {
  const navigate = useNavigate();

  const handleOpenInChat = (result) => {
    if (result?.document_id) {
      navigate(PATHS.newChat, {
        state: { initialDocumentId: result.document_id }
      });
    }
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