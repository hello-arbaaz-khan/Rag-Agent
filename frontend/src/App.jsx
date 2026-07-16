import { useState } from "react";
import ChatArea from "./components/Chat/ChatArea";
import Toast from "./components/Common/Toast";
import Sidebar from "./components/Sidebar/Sidebar";
import UploadModal from "./components/Upload/UploadModal";
import AdvancedSearch from "./components/Search/AdvancedSearch";
import { usePolling } from "./hooks/usePolling";
import { useAppContext } from "./context/AppContext";

const App = () => {
  const [uploadOpen, setUploadOpen] = useState(false);
  const [view, setView] = useState("chat");
  const { dispatch } = useAppContext();
  usePolling();

  const handleOpenInChat = (result) => {
    if (result?.document_id) {
      dispatch({ type: "SET_SELECTED_DOCUMENT", payload: result.document_id });
    }
    setView("chat");
  };

  return (
    <div className="h-screen overflow-hidden bg-brand-bg text-white">
      <div className="flex h-full flex-col lg:flex-row">
        <div className="h-[42vh] min-h-[330px] lg:h-full">
          <Sidebar onUploadClick={() => setUploadOpen(true)} activeView={view} onNavigate={setView} />
        </div>
        <div className="min-h-0 flex-1">
          {view === "search" ? <AdvancedSearch onOpenInChat={handleOpenInChat} /> : <ChatArea />}
        </div>
      </div>
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <Toast />
    </div>
  );
};

export default App;