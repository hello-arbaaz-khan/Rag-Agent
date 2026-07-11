import { useEffect, useRef, useState } from "react";
import { Bot, CheckCircle2, CircleAlert, FileSearch, MessageSquareText, Trash2 } from "lucide-react";
import { useAppContext } from "../../context/AppContext";
import { documentApi } from "../../services/api";
import Badge from "../Common/Badge";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import TypingIndicator from "./TypingIndicator";

const WelcomeScreen = () => (
  <div className="flex h-full items-center justify-center p-6">
    <div className="max-w-xl text-center">
      <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-blue-700 to-violet-700 shadow-lg shadow-blue-950/40">
        <Bot className="h-8 w-8 text-white" />
      </div>
      <h2 className="text-2xl font-extrabold text-white">Ask precise questions about your documents.</h2>
      <p className="mt-3 text-sm leading-6 text-slate-400">
        Upload a PDF, TXT, or DOCX from the sidebar. Once processing is complete, select it and start a document-grounded chat.
      </p>
    </div>
  </div>
);

const EmptyMessages = ({ processing }) => (
  <div className="flex h-full items-center justify-center p-6">
    <div className="max-w-md rounded-xl border border-slate-700 bg-slate-900/55 p-6 text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600/15 text-blue-200">
        {processing ? <FileSearch className="h-6 w-6" /> : <MessageSquareText className="h-6 w-6" />}
      </div>
      <h3 className="font-bold text-white">{processing ? "Document is still processing." : "No messages yet."}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-400">
        {processing
          ? "The chat input will unlock automatically when the document is ready."
          : "Ask a question to generate an answer with source pages and confidence scoring."}
      </p>
    </div>
  </div>
);

const ChatArea = () => {
  const { selectedDocument, chatHistory, dispatch, addToast } = useAppContext();
  const [question, setQuestion] = useState("");
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);
  const isSubmittingRef = useRef(false);

  const messages = selectedDocument ? chatHistory[selectedDocument.id] || [] : [];
  const processing = selectedDocument && !Boolean(selectedDocument.is_processed) && !selectedDocument.processing_error;

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages.length, loadingAnswer, selectedDocument?.id]);

  if (!selectedDocument) return <WelcomeScreen />;

  const handleSubmit = async () => {
    const trimmed = question.trim();
    if (!trimmed || loadingAnswer || processing || isSubmittingRef.current) return;
    
    isSubmittingRef.current = true;

    setError("");
    setQuestion("");
    dispatch({
      type: "ADD_MESSAGE",
      documentId: selectedDocument.id,
      payload: {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
        createdAt: new Date().toISOString()
      }
    });

    setLoadingAnswer(true);
    try {
      const response = await documentApi.askQuestion({
        question: trimmed,
        documentId: selectedDocument.id
      });
      dispatch({
        type: "ADD_MESSAGE",
        documentId: selectedDocument.id,
        payload: {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          // confidence: response.confidence_score,
          // sources: response.source_chunks || [],
          createdAt: new Date().toISOString()
        }
      });
    } catch (answerError) {
      setError(answerError.message);
      addToast(answerError.message, "error");
    } finally {
      setLoadingAnswer(false);
      isSubmittingRef.current = false;
    }
  };

  const handleClearChat = async () => {
    if (!selectedDocument) return;
    try {
      await documentApi.clearChatHistory(selectedDocument.id);
      dispatch({ type: "CLEAR_CHAT", documentId: selectedDocument.id });
      addToast("Chat history cleared successfully.", "success");
    } catch (err) {
      addToast(err.message, "error");
    }
  };

  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-brand-bg">
      <header className="flex flex-col gap-3 border-b border-slate-800 bg-slate-950/65 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h2 className="truncate text-xl font-extrabold text-white">{selectedDocument.name}</h2>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge className="uppercase">{selectedDocument.file_type}</Badge>
            {selectedDocument.processing_error ? (
              <Badge tone="low">
                <CircleAlert className="mr-1 h-3.5 w-3.5" />
                Processing error
              </Badge>
            ) : Boolean(selectedDocument.is_processed) ? (
              <Badge tone="high">
                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                Ready
              </Badge>
            ) : (
              <Badge>Processing</Badge>
            )}
            {selectedDocument.chunk_count !== undefined ? <Badge>{selectedDocument.chunk_count} chunks</Badge> : null}
          </div>
        </div>
        <button
          type="button"
          onClick={handleClearChat}
          disabled={!messages.length}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-sm font-bold text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Trash2 className="h-4 w-4" />
          Clear chat
        </button>
      </header>

      {selectedDocument.processing_error ? (
        <div className="mx-5 mt-4 rounded-xl border border-red-500/30 bg-red-950/30 p-3 text-sm text-red-100">
          {selectedDocument.processing_error}
        </div>
      ) : null}

      {error ? (
        <div className="mx-5 mt-4 rounded-xl border border-red-500/30 bg-red-950/30 p-3 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      <section ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6">
        {messages.length === 0 && !loadingAnswer ? (
          <EmptyMessages processing={processing} />
        ) : (
          <div className="space-y-5">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {loadingAnswer ? (
              <div className="flex gap-3">
                <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-600/20 text-violet-200">
                  <Bot className="h-5 w-5" />
                </div>
                <TypingIndicator />
              </div>
            ) : null}
          </div>
        )}
      </section>

      <ChatInput
        value={question}
        setValue={setQuestion}
        onSubmit={handleSubmit}
        disabled={processing || Boolean(selectedDocument.processing_error)}
        loading={loadingAnswer}
      />
    </main>
  );
};

export default ChatArea;
