import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  CircleAlert,
  FileSearch,
  FileText,
  MessageSquare,
  MessageSquareText,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2
} from "lucide-react";
import { useAppContext } from "../../context/AppContext";
import { useAuth } from "../../context/AuthContext";
import { documentApi } from "../../services/api";
import Badge from "../Common/Badge";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import TypingIndicator from "./TypingIndicator";

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 5) return "Good night";
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
};

const QUICK_ACTIONS = [
  { id: "summarize", icon: FileText, title: "Summarize a document", sub: "Get key points in seconds" },
  { id: "find", icon: Search, title: "Find information", sub: "Search across your files" },
  { id: "ask", icon: MessageSquare, title: "Ask a question", sub: "Get detailed answers" },
  { id: "analyze", icon: Sparkles, title: "Analyze content", sub: "Get insights and summaries" }
];

const WelcomeScreen = ({ value, setValue, onSubmit, onUploadClick, onNavigate, inputRef }) => {
  const { user } = useAuth();
  const firstName = (user?.display_name || user?.username || "there").split(" ")[0];

  const handleQuickAction = (id) => {
    if (id === "find") {
      onNavigate?.("search");
      return;
    }
    if (id === "summarize" || id === "analyze") {
      onUploadClick?.();
      return;
    }
    inputRef?.current?.focus();
  };

  return (
    <div className="flex h-full items-center justify-center overflow-y-auto p-6">
      <div className="w-full max-w-2xl py-10 text-center">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg shadow-blue-950/30">
          <Sparkles className="h-7 w-7 text-white" />
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
          {getGreeting()}, {firstName} <span className="align-middle">👋</span>
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Ask anything from your documents or get help from the AI agent.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-3 text-left sm:grid-cols-2">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.id}
              type="button"
              onClick={() => handleQuickAction(action.id)}
              className="group flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-md dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-blue-500/40"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-300">
                <action.icon className="h-4.5 w-4.5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-800 dark:text-white">{action.title}</p>
                <p className="text-xs text-slate-400 dark:text-slate-500">{action.sub}</p>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-blue-500 dark:text-slate-600" />
            </button>
          ))}
        </div>

        <div className="mt-6 text-left">
          <ChatInput value={value} setValue={setValue} onSubmit={onSubmit} onAttachClick={onUploadClick} floating inputRef={inputRef} />
        </div>

        <div className="mt-8 flex items-center justify-center gap-3 text-xs text-slate-400 dark:text-slate-500">
          <span className="h-px w-16 bg-slate-200 dark:bg-white/10" />
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5" />
            Your data is secure and private
          </span>
          <span className="h-px w-16 bg-slate-200 dark:bg-white/10" />
        </div>
      </div>
    </div>
  );
};

const EmptyMessages = ({ processing }) => (
  <div className="flex h-full items-center justify-center p-6">
    <div className="max-w-md rounded-xl border border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-700 dark:bg-slate-900/55">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-500 dark:bg-blue-600/15 dark:text-blue-200">
        {processing ? <FileSearch className="h-6 w-6" /> : <MessageSquareText className="h-6 w-6" />}
      </div>
      <h3 className="font-bold text-slate-900 dark:text-white">{processing ? "Document is still processing." : "No messages yet."}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
        {processing
          ? "The chat input will unlock automatically when the document is ready."
          : "Ask a question to generate an answer with source pages and confidence scoring."}
      </p>
    </div>
  </div>
);

const ChatArea = ({ onUploadClick, onNavigate }) => {
  const { selectedDocument, chatHistory, dispatch, addToast } = useAppContext();
  const [question, setQuestion] = useState("");
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const isSubmittingRef = useRef(false);

  const messages = selectedDocument ? chatHistory[selectedDocument.id] || [] : [];
  const processing = selectedDocument && !Boolean(selectedDocument.is_processed) && !selectedDocument.processing_error;

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages.length, loadingAnswer, selectedDocument?.id]);

  const handleSubmit = async () => {
    const trimmed = question.trim();
    if (!trimmed || loadingAnswer || processing || isSubmittingRef.current) return;
    if (!selectedDocument) return;

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

  if (!selectedDocument) {
    return (
      <WelcomeScreen
        value={question}
        setValue={setQuestion}
        onSubmit={handleSubmit}
        onUploadClick={onUploadClick}
        onNavigate={onNavigate}
        inputRef={inputRef}
      />
    );
  }

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
    <main className="flex h-full min-w-0 flex-1 flex-col bg-white dark:bg-brand-bg">
      <header className="flex flex-col gap-3 border-b border-slate-200 bg-white/70 px-5 py-4 dark:border-slate-800 dark:bg-slate-950/65 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h2 className="truncate text-xl font-extrabold text-slate-900 dark:text-white">{selectedDocument.name}</h2>
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
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <Trash2 className="h-4 w-4" />
          Clear chat
        </button>
      </header>

      {selectedDocument.processing_error ? (
        <div className="mx-5 mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-500/30 dark:bg-red-950/30 dark:text-red-100">
          {selectedDocument.processing_error}
        </div>
      ) : null}

      {error ? (
        <div className="mx-5 mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-500/30 dark:bg-red-950/30 dark:text-red-100">
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
                <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-500/15 text-violet-500 dark:bg-violet-600/20 dark:text-violet-200">
                  <Bot className="h-5 w-5" />
                </div>
                <TypingIndicator />
              </div>
            ) : null}
          </div>
        )}
      </section>

      <div className="p-4">
        <ChatInput
          value={question}
          setValue={setQuestion}
          onSubmit={handleSubmit}
          disabled={processing || Boolean(selectedDocument.processing_error)}
          loading={loadingAnswer}
          onAttachClick={onUploadClick}
          floating
        />
      </div>
    </main>
  );
};

export default ChatArea;