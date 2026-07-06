const confidenceStyles = {
  low: "border-red-400/30 bg-red-500/15 text-red-200",
  medium: "border-yellow-400/30 bg-yellow-500/15 text-yellow-100",
  high: "border-emerald-400/30 bg-emerald-500/15 text-emerald-100",
  neutral: "border-slate-500/40 bg-slate-700/60 text-slate-200"
};

export const getConfidenceLevel = (score) => {
  if (score >= 0.7) return "high";
  if (score >= 0.5) return "medium";
  if (typeof score === "number") return "low";
  return "neutral";
};

const Badge = ({ children, tone = "neutral", className = "" }) => (
  <span
    className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${confidenceStyles[tone]} ${className}`}
  >
    {children}
  </span>
);

export default Badge;
