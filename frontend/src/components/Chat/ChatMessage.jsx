import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, UserRound, RotateCw, AlertCircle } from "lucide-react";
import Badge, { getConfidenceLevel } from "../Common/Badge";

const pageSummary = (sources = []) => {
  const pages = [
    ...new Set(
      sources
        .map((source) => source.page_number)
        .filter((page) => page !== undefined && page !== null)
    ),
  ];

  if (!pages.length) return null;

  return `Sources: page${pages.length > 1 ? "s" : ""} ${pages.join(", ")}`;
};

const MarkdownContent = ({ content }) => (
  <div
    className="
      markdown-content min-w-0 break-words
      [&>*:first-child]:mt-0
      [&>*:last-child]:mb-0
      [&_h1]:mb-3 [&_h1]:mt-5 [&_h1]:text-xl [&_h1]:font-bold
      [&_h2]:mb-2 [&_h2]:mt-5 [&_h2]:text-lg [&_h2]:font-semibold
      [&_h3]:mb-2 [&_h3]:mt-4 [&_h3]:text-base [&_h3]:font-semibold
      [&_p]:mb-3 [&_p]:leading-7
      [&_ul]:mb-3 [&_ul]:list-disc [&_ul]:pl-6
      [&_ol]:mb-3 [&_ol]:list-decimal [&_ol]:pl-6
      [&_li]:my-1 [&_li]:pl-1
      [&_strong]:font-bold
      [&_blockquote]:my-3 [&_blockquote]:border-l-4
      [&_blockquote]:border-slate-500 [&_blockquote]:pl-4
      [&_pre]:my-3 [&_pre]:overflow-x-auto
      [&_pre]:rounded-lg [&_pre]:bg-slate-950
      [&_pre]:p-4 [&_pre]:text-slate-100
      [&_code]:break-words [&_code]:font-mono [&_code]:text-[0.9em]
      [&_pre_code]:break-normal
      [&_a]:underline [&_a]:underline-offset-2
      [&_table]:my-3 [&_table]:w-full [&_table]:border-collapse
      [&_th]:border [&_th]:border-slate-600 [&_th]:px-3 [&_th]:py-2
      [&_th]:font-semibold
      [&_td]:border [&_td]:border-slate-600 [&_td]:px-3 [&_td]:py-2
      [&_hr]:my-4 [&_hr]:border-slate-600
    "
  >
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ children, href, ...props }) => {
          const safeHref =
            typeof href === "string" &&
            /^(https?:|mailto:)/i.test(href)
              ? href
              : undefined;

          return (
            <a
              {...props}
              href={safeHref}
              target={safeHref ? "_blank" : undefined}
              rel={safeHref ? "noopener noreferrer" : undefined}
            >
              {children}
            </a>
          );
        },
      }}
    >
      {typeof content === "string" ? content : ""}
    </ReactMarkdown>
  </div>
);

const ChatMessage = ({ message, onRetry }) => {
  const isUser = message.role === "user";
  const isPending = message.status === "pending";
  const isFailed = message.status === "failed";
  const confidenceLevel = getConfidenceLevel(message.confidence);
  const sources = pageSummary(message.sources);

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-600/20 text-violet-200">
          <Bot className="h-5 w-5" />
        </div>
      )}

      <div
        className={`flex min-w-0 max-w-[88%] flex-col gap-2 sm:max-w-[75%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div
          className={`min-w-0 max-w-full rounded-xl px-4 py-3 text-sm leading-6 shadow-lg ${
            isUser
              ? "bg-gradient-to-r from-blue-700 to-violet-700 text-white shadow-blue-950/30"
              : "border border-slate-700 bg-slate-800 text-slate-100 shadow-slate-950/30"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">
              {message.content}
            </p>
          ) : isPending ? (
            <div
              className="flex items-center gap-3"
              role="status"
              aria-live="polite"
            >
              <span className="inline-flex items-center gap-1">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.25s]" />              </span>
            </div>
          ) : isFailed ? (
            <div className="flex flex-col items-start gap-3">
              <div className="flex items-center gap-2 text-sm text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  Unable to generate your answer. Please try again.
                </span>
              </div>

              {onRetry && (
                <button
                  type="button"
                  onClick={() => onRetry(message)}
                  className="inline-flex items-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-sm transition-colors hover:bg-slate-700"
                >
                  <RotateCw className="h-4 w-4" />
                  Retry
                </button>
              )}
            </div>
          ) : (
            <MarkdownContent content={message.content} />
          )}
        </div>

        {!isUser && !isPending && !isFailed && (
          <div className="flex flex-wrap items-center gap-2">
            {typeof message.confidence === "number" && (
              <Badge tone={confidenceLevel}>
                {confidenceLevel === "high"
                  ? "High"
                  : confidenceLevel === "medium"
                    ? "Medium"
                    : "Low"}{" "}
                confidence {Math.round(message.confidence * 100)}%
              </Badge>
            )}

            {sources && <Badge>{sources}</Badge>}
          </div>
        )}
      </div>

      {isUser && (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600/20 text-blue-200">
          <UserRound className="h-5 w-5" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;