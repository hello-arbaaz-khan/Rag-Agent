import { useState } from "react";
import ChatArea from "./components/Chat/ChatArea";
import Toast from "./components/Common/Toast";
import Sidebar from "./components/Sidebar/Sidebar";
import UploadModal from "./components/Upload/UploadModal";
import { usePolling } from "./hooks/usePolling";

const App = () => {
  const [uploadOpen, setUploadOpen] = useState(false);
  usePolling();

  return (
    <div className="h-screen overflow-hidden bg-brand-bg text-white">
      <div className="flex h-full flex-col lg:flex-row">
        <div className="h-[42vh] min-h-[330px] lg:h-full">
          <Sidebar onUploadClick={() => setUploadOpen(true)} />
        </div>
        <div className="min-h-0 flex-1">
          <ChatArea />
        </div>
      </div>
      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <Toast />
    </div>
  );
};

export default App;
