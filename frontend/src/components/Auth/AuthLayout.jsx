const AuthLayout = ({ title, subtitle, children }) => (
  <div className="flex min-h-screen items-center justify-center bg-brand-bg px-4 py-10 font-sans">
    <div className="w-full max-w-md rounded-2xl border border-white/10 bg-brand-card p-8 shadow-soft">
      <h1 className="text-2xl font-semibold text-white">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-white/60">{subtitle}</p>}
      <div className="mt-6">{children}</div>
    </div>
  </div>
);

export default AuthLayout;