import { useState } from "react";
import ChatArea from "./components/Chat/ChatArea";
import Toast from "./components/Common/Toast";
import Sidebar from "./components/Sidebar/Sidebar";
import TopBar from "./components/Sidebar/TopBar";
import QuickInfoPanel from "./components/Sidebar/QuickInfoPanel";
import UploadModal from "./components/Upload/UploadModal";
import AdvancedSearch from "./components/Search/AdvancedSearch";
import DocumentsView from "./components/Documents/DocumentsView";
import ChangePasswordPage from "./components/Auth/ChangePasswordPage";
import DriveConnection from "./components/Drive/DriveConnection";
import { usePolling } from "./hooks/usePolling";
import { useDriveAutoSync } from "./hooks/useDriveAutoSync";
import { useAppContext } from "./context/AppContext";

const App = () => {
  const [uploadOpen, setUploadOpen] = useState(false);
  const [view, setView] = useState("chat");
  const [quickInfoOpen, setQuickInfoOpen] = useState(true);
  const { dispatch } = useAppContext();
  useDriveAutoSync();
  usePolling();

  const handleOpenInChat = (result) => {
    if (result?.document_id) {
      dispatch({ type: "SET_SELECTED_DOCUMENT", payload: result.document_id });
    }
    setView("chat");
  };

  return (
    <div className="h-screen overflow-hidden bg-white text-slate-900 dark:bg-brand-bg dark:text-white">
      <div className="flex h-full flex-col lg:flex-row">
        <div className="h-[42vh] min-h-[330px] lg:h-full">
          <Sidebar onUploadClick={() => setUploadOpen(true)} activeView={view} onNavigate={setView} />
        </div>

        <div className="flex min-h-0 flex-1 flex-col">
          <TopBar onNavigate={setView} quickInfoOpen={quickInfoOpen} onToggleQuickInfo={() => setQuickInfoOpen((open) => !open)} />

          <div className="flex min-h-0 flex-1">
            <div className="min-h-0 flex-1 overflow-y-auto">
              {view === "search" ? <AdvancedSearch onOpenInChat={handleOpenInChat} /> : null}
              {view === "documents" ? (
                <DocumentsView onUploadClick={() => setUploadOpen(true)} onOpenInChat={() => setView("chat")} />
              ) : null}
              {view === "settings" ? (
                <div className="flex min-h-full flex-col items-center gap-6 p-6">
                  <DriveConnection />
                  <ChangePasswordPage onDone={() => setView("chat")} />
                </div>
              ) : null}
              {view === "chat" ? (
                <ChatArea onUploadClick={() => setUploadOpen(true)} onNavigate={setView} />
              ) : null}
            </div>

            {quickInfoOpen ? (
              <div className="hidden lg:block">
                <QuickInfoPanel onClose={() => setQuickInfoOpen(false)} onNavigate={setView} />
              </div>
            ) : null}
          </div>
        </div>
      </div>
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <Toast />
    </div>
  );
};

export default App;