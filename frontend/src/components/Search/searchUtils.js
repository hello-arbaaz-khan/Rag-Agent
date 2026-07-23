export const timeAgo = (dateString) => {
  if (!dateString) return "—";
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "—";

  const diffMs = Date.now() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin} min${diffMin === 1 ? "" : "s"} ago`;
  if (diffHr < 24) return `${diffHr} hour${diffHr === 1 ? "" : "s"} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? "" : "s"} ago`;
  const diffWeek = Math.floor(diffDay / 7);
  if (diffWeek < 5) return `${diffWeek} week${diffWeek === 1 ? "" : "s"} ago`;
  const diffMonth = Math.floor(diffDay / 30);
  if (diffMonth < 12) return `${diffMonth} month${diffMonth === 1 ? "" : "s"} ago`;
  const diffYear = Math.floor(diffDay / 365);
  return `${diffYear} year${diffYear === 1 ? "" : "s"} ago`;
};

export const mimeToLabel = (mimeType) => {
  if (!mimeType) return "FILE";
  if (mimeType.includes("pdf")) return "PDF";
  if (mimeType.includes("wordprocessingml") || mimeType.includes("msword")) return "DOCX";
  if (mimeType.includes("text/plain")) return "TXT";
  if (mimeType.includes("spreadsheet")) return "XLSX";
  if (mimeType.includes("presentation")) return "PPTX";
  return mimeType.split("/").pop()?.slice(0, 5).toUpperCase() || "FILE";
};

export const syncStatusStyles = {
  indexed: "border-emerald-400/30 bg-emerald-500/15 text-emerald-200",
  processing: "border-blue-400/30 bg-blue-500/15 text-blue-200",
  pending: "border-yellow-400/30 bg-yellow-500/15 text-yellow-100",
  failed: "border-red-400/30 bg-red-500/15 text-red-200"
};

export const relevanceTone = (score) => {
  if (typeof score !== "number") return "border-slate-500/40 bg-slate-700/60 text-slate-200";
  if (score >= 0.6) return "border-emerald-400/30 bg-emerald-500/15 text-emerald-200";
  if (score >= 0.4) return "border-blue-400/30 bg-blue-500/15 text-blue-200";
  return "border-yellow-400/30 bg-yellow-500/15 text-yellow-100";
};
