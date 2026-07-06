const TypingIndicator = () => (
  <div className="flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-800 px-4 py-3">
    {[0, 1, 2].map((dot) => (
      <span
        key={dot}
        className="h-2 w-2 animate-bounce rounded-full bg-slate-300"
        style={{ animationDelay: `${dot * 120}ms` }}
      />
    ))}
  </div>
);

export default TypingIndicator;

