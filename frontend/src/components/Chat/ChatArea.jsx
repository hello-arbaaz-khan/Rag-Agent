
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  CheckCircle2,
  FileText,
  Paperclip,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAppContext } from "../../context/AppContext";
import { useAuth } from "../../context/AuthContext";
import { conversationApi, documentApi } from "../../services/api";
import { PATHS } from "../../router/paths";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";

const makeTitle = (message) => {
  const cleaned = message.replace(/\s+/g, " ").trim();
  if (!cleaned) return "New chat";

  return cleaned.length > 60
    ? `${cleaned.slice(0, 57).trimEnd()}...`
    : cleaned;
};

const makeOptimisticId = (role) =>
  `local-${role}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

const findCompletedPair = (messages, question) => {
  for (let i = messages.length - 2; i >= 0; i -= 1) {
    if (
      messages[i]?.role === "user" &&
      messages[i]?.content?.trim() === question.trim() &&
      messages[i + 1]?.role === "assistant" &&
      messages[i + 1]?.content?.trim()
    ) {
      return true;
    }
  }

  return false;
};

const WelcomeScreen = () => {
  const { user } = useAuth();
  const firstName = (
    user?.display_name ||
    user?.username ||
    ""
  ).split(" ")[0];

  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className="max-w-xl text-center">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600">
          <Sparkles className="h-7 w-7 text-white" />
        </div>

        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
          What would you like to know
          {firstName ? `, ${firstName}` : ""}?
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">
          Select existing documents or upload multiple files, then ask
          questions across them. Your chat will be saved when you send
          your first message.
        </p>
      </div>
    </div>
  );
};

const ChatArea = ({ conversationId, onUploadClick }) => {
  const {
    documents,
    activeConversation,
    messages,
    loadingMessages,
    dispatch,
    addToast,
    loadDocuments,
    loadConversations,
    loadConversation,
  } = useAppContext();

  const location = useLocation();
  const navigate = useNavigate();

  const [question, setQuestion] = useState("");
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const [showDocumentPicker, setShowDocumentPicker] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [error, setError] = useState("");
  const [optimisticTurn, setOptimisticTurn] = useState(null);

  const fileInputRef = useRef(null);
  const scrollRef = useRef(null);
  const submitLock = useRef(false);

  const currentConversation =
    Number(conversationId) === Number(activeConversation?.id)
      ? activeConversation
      : null;

  useEffect(() => {
    let cancelled = false;

    if (!conversationId) {
      dispatch({ type: "RESET_CHAT" });
      setOptimisticTurn(null);

      const initialDocumentId = Number(
        location.state?.initialDocumentId
      );

      setSelectedDocumentIds(
        Number.isInteger(initialDocumentId) && initialDocumentId > 0
          ? [initialDocumentId]
          : []
      );

      setError("");
      setQuestion("");
      return undefined;
    }

    setError("");
    dispatch({ type: "SET_MESSAGES_LOADING", payload: true });

    loadConversation(conversationId)
      .then((conversation) => {
        if (cancelled) return;

        setSelectedDocumentIds(
          (conversation.documents || []).map((doc) => Number(doc.id))
        );
      })
      .catch((loadError) => {
        if (cancelled) return;

        setError(loadError.message);
        addToast(loadError.message, "error");
        navigate(PATHS.newChat, { replace: true });
      });

    return () => {
      cancelled = true;
    };
  }, [
    conversationId,
    loadConversation,
    dispatch,
    addToast,
    navigate,
    location.state,
  ]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length, loadingAnswer, optimisticTurn?.assistantMessage?.status]);

  const selectedDocuments = useMemo(
    () =>
      documents.filter((doc) =>
        selectedDocumentIds.includes(Number(doc.id))
      ),
    [documents, selectedDocumentIds]
  );

  const allDocumentsReady =
    selectedDocuments.length > 0 &&
    selectedDocuments.length === selectedDocumentIds.length &&
    selectedDocuments.every(
      (doc) => Boolean(doc.is_processed) && !doc.processing_error
    );

  const toggleDocument = (documentId) => {
    const id = Number(documentId);

    setSelectedDocumentIds((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  };

  const handleUploadFiles = async (event) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";

    if (!files.length) return;

    const tooLarge = files.find(
      (file) => file.size > 50 * 1024 * 1024
    );

    if (tooLarge) {
      setError(`${tooLarge.name} exceeds the 50MB file limit.`);
      return;
    }

    setUploading(true);
    setError("");

    try {
      const uploadedIds = [];

      for (const file of files) {
        const result = await documentApi.uploadDocument(file);
        const document = result?.data ?? result;

        if (!document?.id) {
          throw new Error(
            `The upload response for ${file.name} did not contain a document ID.`
          );
        }

        uploadedIds.push(Number(document.id));

        dispatch({
          type: "UPSERT_DOCUMENT",
          payload: document,
        });
      }

      await loadDocuments();

      setSelectedDocumentIds((current) =>
        [...new Set([...current, ...uploadedIds])]
      );

      addToast(
        `${uploadedIds.length} file${uploadedIds.length === 1 ? "" : "s"} uploaded. Wait for processing to finish before asking questions.`,
        "success"
      );
    } catch (uploadError) {
      setError(uploadError.message);
      addToast(uploadError.message, "error");
    } finally {
      setUploading(false);
    }
  };

  /*
   * Handles both first sends and retries.
   *
   * The optimistic user message is kept visible until a saved response
   * is loaded or the user retries successfully.
   */
  const sendTurn = async ({
    questionText,
    targetConversationId,
    documentIds,
    userMessageId,
    isRetry = false,
  }) => {
    if (submitLock.current) return;

    submitLock.current = true;
    setLoadingAnswer(true);
    setError("");

    setOptimisticTurn((current) =>
      current
        ? {
            ...current,
            conversationId: targetConversationId ?? current.conversationId,
            assistantMessage: {
              ...current.assistantMessage,
              status: "pending",
              content: "",
              error: "",
            },
          }
        : current
    );

    let conversationIdForRecovery = targetConversationId ?? null;

    try {
      let conversation = conversationIdForRecovery
        ? await conversationApi.get(conversationIdForRecovery)
        : null;

      const isNewConversation = !conversation;

      if (!conversation) {
        conversation = await conversationApi.create({
          title: makeTitle(questionText),
          documentIds,
        });

        conversationIdForRecovery = conversation.id;

        dispatch({
          type: "UPSERT_CONVERSATION",
          payload: conversation,
        });

        setOptimisticTurn((current) =>
          current
            ? { ...current, conversationId: conversation.id }
            : current
        );

        // Navigate as soon as the conversation exists, not after
        // generation finishes. This keeps the chat and sidebar responsive.
        navigate(PATHS.chat(conversation.id), {
          replace: true,
          state: null,
        });
      } else {
        const attachedIds = (conversation.documents || []).map(
          (doc) => Number(doc.id)
        );

        const missingIds = documentIds.filter(
          (id) => !attachedIds.includes(Number(id))
        );

        if (missingIds.length) {
          await conversationApi.attachDocuments(
            conversation.id,
            missingIds
          );

          conversation = await conversationApi.get(conversation.id);

          dispatch({
            type: "UPSERT_CONVERSATION",
            payload: conversation,
          });
        }
      }

      /*
       * On retry, first check whether the server already saved the answer.
       * This helps recover when the server finished but the response was lost.
       */
      if (isRetry) {
        try {
          const savedMessages = await conversationApi.listMessages(
            conversation.id
          );

          if (findCompletedPair(savedMessages, questionText)) {
            dispatch({
              type: "SET_MESSAGES",
              payload: savedMessages,
            });

            setOptimisticTurn(null);
            await loadConversations();
            return;
          }
        } catch {
          // If the check itself fails, allow the user to retry the request.
        }
      }

      await conversationApi.sendMessage(
        conversation.id,
        questionText
      );

      const latestMessages = await conversationApi.listMessages(
        conversation.id
      );

      dispatch({
        type: "SET_MESSAGES",
        payload: latestMessages,
      });

      setOptimisticTurn(null);
      await loadConversations();

      if (isNewConversation) {
        navigate(PATHS.chat(conversation.id), {
          replace: true,
          state: null,
        });
      }
    } catch (submitError) {
      /*
       * A timeout or disconnected browser does not always mean the backend
       * failed. Check whether the answer was saved before showing Retry.
       */
      let recovered = false;

      if (conversationIdForRecovery) {
        try {
          const savedMessages = await conversationApi.listMessages(
            conversationIdForRecovery
          );

          if (findCompletedPair(savedMessages, questionText)) {
            dispatch({
              type: "SET_MESSAGES",
              payload: savedMessages,
            });

            setOptimisticTurn(null);
            recovered = true;
          }
        } catch {
          // Keep the local message and offer retry below.
        }
      }

      if (!recovered) {
        setError(
          "The answer could not be confirmed. Your question is still here; try again when your connection is available."
        );

        setOptimisticTurn((current) =>
          current
            ? {
                ...current,
                conversationId:
                  conversationIdForRecovery ?? current.conversationId,
                assistantMessage: {
                  ...current.assistantMessage,
                  status: "failed",
                  content:
                    "I couldn't confirm the answer. Your question is saved here in the chat. You can retry.",
                  error: submitError.message,
                },
              }
            : current
        );
      }
    } finally {
      setLoadingAnswer(false);
      submitLock.current = false;
    }
  };

  const handleSubmit = async () => {
    const trimmed = question.trim();

    if (
      !trimmed ||
      loadingAnswer ||
      uploading ||
      submitLock.current
    ) {
      return;
    }

    if (!selectedDocumentIds.length) {
      setError(
        "Select at least one document or upload a file before sending a question."
      );
      setShowDocumentPicker(true);
      return;
    }

    const selected = documents.filter((doc) =>
      selectedDocumentIds.includes(Number(doc.id))
    );

    if (
      selected.length !== selectedDocumentIds.length ||
      selected.some(
        (doc) => !doc.is_processed || doc.processing_error
      )
    ) {
      setError(
        "Wait until every selected document has finished processing successfully."
      );
      return;
    }

    const turn = {
      question: trimmed,
      conversationId: currentConversation?.id ?? null,
      documentIds: [...selectedDocumentIds],
      userMessage: {
        id: makeOptimisticId("user"),
        role: "user",
        content: trimmed,
      },
      assistantMessage: {
        id: makeOptimisticId("assistant"),
        role: "assistant",
        content: "",
        status: "pending",
      },
    };

    setOptimisticTurn(turn);
    setQuestion("");
    setError("");

    await sendTurn({
      questionText: turn.question,
      targetConversationId: turn.conversationId,
      documentIds: turn.documentIds,
      userMessageId: turn.userMessage.id,
    });
  };

  const handleRetry = async () => {
    if (!optimisticTurn || loadingAnswer || submitLock.current) return;

    await sendTurn({
      questionText: optimisticTurn.question,
      targetConversationId: optimisticTurn.conversationId,
      documentIds: optimisticTurn.documentIds,
      userMessageId: optimisticTurn.userMessage.id,
      isRetry: true,
    });
  };

  const handleDeleteConversation = async () => {
    if (!currentConversation) return;

    if (
      !window.confirm("Delete this conversation and its messages?")
    ) {
      return;
    }

    try {
      await conversationApi.delete(currentConversation.id);

      dispatch({
        type: "REMOVE_CONVERSATION",
        payload: currentConversation.id,
      });

      setOptimisticTurn(null);
      await loadConversations();
      navigate(PATHS.newChat, { replace: true });
      addToast("Conversation deleted.", "success");
    } catch (deleteError) {
      addToast(deleteError.message, "error");
    }
  };

  const handleSend = (event) => {
    event?.preventDefault?.();
    handleSubmit();
  };

  const displayedMessages = optimisticTurn
    ? [
        ...messages,
        optimisticTurn.userMessage,
        optimisticTurn.assistantMessage,
      ]
    : messages;

  return (
    <main className="flex h-full min-w-0 flex-1 flex-col bg-white dark:bg-brand-bg">
      <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-bold text-slate-900 dark:text-white">
            {currentConversation?.title || "New chat"}
          </h2>

          <p className="text-xs text-slate-500 dark:text-slate-400">
            {selectedDocuments.length
              ? `${selectedDocuments.length} document${selectedDocuments.length === 1 ? "" : "s"} selected`
              : "No documents selected"}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={() => setShowDocumentPicker((open) => !open)}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-white/10 dark:text-slate-200 dark:hover:bg-white/5"
          >
            <Plus className="h-4 w-4" />
            Documents
          </button>

          {currentConversation ? (
            <button
              type="button"
              onClick={handleDeleteConversation}
              title="Delete conversation"
              className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-red-50 hover:text-red-600 dark:border-white/10 dark:text-slate-300 dark:hover:bg-red-500/10"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          ) : null}
        </div>
      </header>

      {showDocumentPicker ? (
        <section className="border-b border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/40">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800 dark:text-white">
              Choose documents
            </h3>

            <button
              type="button"
              onClick={() => setShowDocumentPicker(false)}
              aria-label="Close document picker"
              className="rounded-lg p-1 text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="max-h-48 space-y-1 overflow-y-auto">
            {documents.map((doc) => (
              <label
                key={doc.id}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-2 hover:bg-white dark:hover:bg-white/5"
              >
                <input
                  type="checkbox"
                  checked={selectedDocumentIds.includes(Number(doc.id))}
                  onChange={() => toggleDocument(doc.id)}
                  className="h-4 w-4 accent-blue-600"
                />

                <FileText className="h-4 w-4 shrink-0 text-slate-400" />

                <span className="min-w-0 flex-1 truncate text-sm text-slate-700 dark:text-slate-200">
                  {doc.name}
                </span>

                {doc.processing_error ? (
                  <span className="text-xs text-red-500">Failed</span>
                ) : doc.is_processed ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-600">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Ready
                  </span>
                ) : (
                  <span className="text-xs text-amber-600">
                    Processing
                  </span>
                )}
              </label>
            ))}

            {!documents.length ? (
              <p className="py-3 text-sm text-slate-500">
                No uploaded documents yet.
              </p>
            ) : null}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md,.csv,.xlsx,.pptx"
              onChange={handleUploadFiles}
              className="hidden"
            />

            <button
              type="button"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
            >
              <Paperclip className="h-4 w-4" />
              {uploading ? "Uploading..." : "Upload files"}
            </button>

            <button
              type="button"
              onClick={() => setShowDocumentPicker(false)}
              className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 dark:border-white/10 dark:text-slate-300"
            >
              Done
            </button>
          </div>

          {selectedDocuments.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedDocuments.map((doc) => (
                <span
                  key={doc.id}
                  className="inline-flex max-w-full items-center gap-2 rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800 dark:bg-blue-500/15 dark:text-blue-200"
                >
                  <span className="max-w-52 truncate">{doc.name}</span>
                  <button
                    type="button"
                    onClick={() => toggleDocument(doc.id)}
                    aria-label={`Remove ${doc.name}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {error ? (
        <div className="mx-4 mt-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-950/30 dark:text-red-200">
          {error}
        </div>
      ) : null}

      <section
        ref={scrollRef}
        className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6"
      >
        {!conversationId && !displayedMessages.length && !loadingAnswer ? (
          <WelcomeScreen />
        ) : loadingMessages && !optimisticTurn ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Loading conversation...
          </div>
        ) : !displayedMessages.length && !loadingAnswer ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Send a message to start this conversation.
          </div>
        ) : (
          <div className="space-y-5">
            {displayedMessages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onRetry={
                  message.id === optimisticTurn?.assistantMessage?.id
                    ? handleRetry
                    : undefined
                }
                retryDisabled={loadingAnswer}
              />
            ))}
          </div>
        )}
      </section>

      <div className="border-t border-slate-200 p-4 dark:border-slate-800">
        {selectedDocuments.length > 0 && !allDocumentsReady ? (
          <p className="mb-2 text-xs text-amber-600 dark:text-amber-300">
            Wait until every selected document has finished processing.
          </p>
        ) : null}

        <ChatInput
          value={question}
          setValue={setQuestion}
          onSubmit={handleSend}
          loading={loadingAnswer || uploading}
          disabled={
            selectedDocuments.length > 0 && !allDocumentsReady
          }
          onAttachClick={() => setShowDocumentPicker((open) => !open)}
          floating
        />

        {!selectedDocumentIds.length ? (
          <p className="mt-2 text-center text-xs text-slate-500">
            Select one or more documents before sending your first message.
          </p>
        ) : null}
      </div>
    </main>
  );
};

export default ChatArea;