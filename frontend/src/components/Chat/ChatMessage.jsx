import { Bot, UserRound } from "lucide-react";
import Badge, { getConfidenceLevel } from "../Common/Badge";

const pageSummary = (sources = []) => {
  const pages = [...new Set(sources.map((source) => source.page_number).filter((page) => page !== undefined && page !== null))];
  if (!pages.length) return null;
  return `Sources: page${pages.length > 1 ? "s" : ""} ${pages.join(", ")}`;
};

const ChatMessage = ({ message }) => {
  const isUser = message.role === "user";
  const confidenceLevel = getConfidenceLevel(message.confidence);

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser ? (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-600/20 text-violet-200">
          <Bot className="h-5 w-5" />
        </div>
      ) : null}

      <div className={`max-w-[88%] sm:max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-2`}>
        <div
          className={`rounded-xl px-4 py-3 text-sm leading-6 shadow-lg ${
            isUser
              ? "bg-gradient-to-r from-blue-700 to-violet-700 text-white shadow-blue-950/30"
              : "border border-slate-700 bg-slate-800 text-slate-100 shadow-slate-950/30"
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {!isUser ? (
          <div className="flex flex-wrap items-center gap-2">
            {typeof message.confidence === "number" ? (
              <Badge tone={confidenceLevel}>
                {confidenceLevel === "high" ? "High" : confidenceLevel === "medium" ? "Medium" : "Low"} confidence
                {" "}
                {Math.round(message.confidence * 100)}%
              </Badge>
            ) : null}
            {pageSummary(message.sources) ? <Badge>{pageSummary(message.sources)}</Badge> : null}
          </div>
        ) : null}
      </div>

      {isUser ? (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600/20 text-blue-200">
          <UserRound className="h-5 w-5" />
        </div>
      ) : null}
    </div>
  );
};

export default ChatMessage;
