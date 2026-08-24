const AuthLayout = ({ title, subtitle, children }) => (
  <div className="flex min-h-screen items-center justify-center bg-brand-bg px-4 py-10 font-sans">
    <div className="w-full max-w-md rounded-2xl border border-white/10 bg-brand-card p-8 shadow-soft">
      <h1 className="text-2xl font-semibold text-white">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-white/60">{subtitle}</p>}
      <div className="mt-6">{children}</div>
    </div>
  </div>
);

export const SplitAuthLayout = ({
  title,
  highlight,
  description,
  illustration,
  features,
  formTitle,
  formSubtitle,
  footer,
  children
}) => (
  <div className="flex min-h-screen font-sans">
    {/* Left side - Illustration */}
    <div className="hidden bg-gradient-to-br from-slate-900 via-slate-800 to-brand-bg px-8 py-12 lg:flex lg:w-1/2 lg:flex-col lg:justify-between">
      <div>
        <h1 className="text-4xl font-bold leading-tight text-white">
          {title} <span className="text-blue-400">{highlight}</span>
        </h1>
        <p className="mt-6 text-lg leading-relaxed text-slate-300">{description}</p>

        {features && (
          <div className="mt-12 space-y-6">
            {features.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <div key={i} className="flex items-start gap-4">
                  <div className="mt-1 rounded-lg bg-blue-500/20 p-2.5 text-blue-300">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-white">{feature.title}</p>
                    <p className="mt-1 text-sm text-slate-400">{feature.sub}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {illustration && (
        <div className="relative h-32 w-full">
          {illustration}
        </div>
      )}
    </div>

    {/* Right side - Form */}
    <div className="flex w-full items-center justify-center bg-white px-4 py-10 dark:bg-brand-card lg:w-1/2">
      <div className="w-full max-w-sm">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{formTitle}</h2>
          {formSubtitle && (
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{formSubtitle}</p>
          )}
        </div>

        <div className="mt-6">{children}</div>

        {footer && <div className="mt-6">{footer}</div>}
      </div>
    </div>
  </div>
);

export const CenteredAuthLayout = ({ icon: Icon, title, subtitle, children }) => (
  <div className="flex min-h-screen items-center justify-center bg-brand-bg px-4 py-10 font-sans">
    <div className="w-full max-w-md rounded-2xl border border-white/10 bg-brand-card p-8 shadow-soft">
      {Icon && (
        <div className="mb-6 flex justify-center">
          <div className="rounded-xl bg-blue-500/20 p-3 text-blue-300">
            <Icon className="h-6 w-6" />
          </div>
        </div>
      )}
      <h1 className="text-center text-2xl font-semibold text-white">{title}</h1>
      {subtitle && <p className="mt-2 text-center text-sm text-white/60">{subtitle}</p>}
      <div className="mt-6">{children}</div>
    </div>
  </div>
);

export default AuthLayout;