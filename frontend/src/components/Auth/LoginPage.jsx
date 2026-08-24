import { useState } from "react";
import { Lock, LogIn, Mail, ShieldCheck, Sparkles, Zap } from "lucide-react";
import { SplitAuthLayout } from "./AuthLayout";
import AuthField from "./AuthField";
import { DocumentsIllustration } from "./AuthIllustrations";
import { authApi } from "../../services/authApi";
import { useAuth } from "../../context/AuthContext";

const FEATURES = [
  { icon: Zap, title: "Smart Search", sub: "Find information instantly" },
  { icon: Sparkles, title: "RAG Powered", sub: "Get accurate answers" },
  { icon: ShieldCheck, title: "Secure", sub: "Your data stays private" }
];

const LoginPage = ({ onNavigate }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.login({ email, password });
      login(res.data.user, res.data.tokens);
    } catch (err) {
      // Backend returns 403 "Account not verified..." for unverified signups —
      // send the user straight to OTP verification instead of just erroring.
      if (err.message.toLowerCase().includes("not verified")) {
        onNavigate("verify-otp", { email });
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SplitAuthLayout
      title="Your documents,"
      highlight="smarter answers."
      description="Upload, search and chat with your files using advanced RAG technology."
      illustration={<DocumentsIllustration />}
      features={FEATURES}
      formTitle="Welcome back"
      formSubtitle="Sign in to your RAG Agent account"
      footer={
        <>
          Don&apos;t have an account?{" "}
          <button type="button" onClick={() => onNavigate("signup")} className="font-semibold text-blue-600 hover:underline dark:text-blue-400">
            Sign up
          </button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
        <AuthField
          label="Email address"
          icon={Mail}
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          name="login-email"
          autoComplete="off"
        />
        <AuthField
          label="Password"
          icon={Lock}
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          name="login-password"
          autoComplete="new-password"
        />

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 dark:border-white/20 dark:bg-white/10"
            />
            Remember me
          </label>
          <button
            type="button"
            onClick={() => onNavigate("forgot-password")}
            className="font-medium text-blue-600 hover:underline dark:text-blue-400"
          >
            Forgot password?
          </button>
        </div>

        {error ? <p className="text-sm text-red-500 dark:text-red-400">{error}</p> : null}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <LogIn className="h-4 w-4" />
          {loading ? "Signing in…" : "Sign in"}
        </button>

        <div className="relative py-1 text-center text-xs">
          <span className="relative bg-white px-3 text-slate-400 dark:bg-brand-card dark:text-slate-500">or continue with</span>
          <div className="absolute inset-x-0 top-1/2 -z-10 h-px bg-slate-200 dark:bg-white/10" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            title="Coming soon"
            className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:hover:bg-white/[0.06]"
          >
            <GoogleIcon />
            Google
          </button>
          <button
            type="button"
            title="Coming soon"
            className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:hover:bg-white/[0.06]"
          >
            <GithubIcon />
            GitHub
          </button>
        </div>
      </form>
    </SplitAuthLayout>
  );
};

const GoogleIcon = () => (
  <svg className="h-4 w-4" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M23.52 12.27c0-.82-.07-1.6-.2-2.36H12v4.47h6.47c-.28 1.5-1.13 2.77-2.4 3.63v3h3.88c2.27-2.09 3.57-5.17 3.57-8.74z"
    />
    <path
      fill="#34A853"
      d="M12 24c3.24 0 5.96-1.07 7.95-2.9l-3.88-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.96H1.27v3.11C3.25 21.3 7.31 24 12 24z"
    />
    <path fill="#FBBC05" d="M5.27 14.29a7.2 7.2 0 0 1 0-4.58V6.6H1.27a12 12 0 0 0 0 10.8z" />
    <path
      fill="#EA4335"
      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.44-3.44C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.6l4 3.11C6.22 6.86 8.87 4.75 12 4.75z"
    />
  </svg>
);

const GithubIcon = () => (
  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 .5C5.65.5.5 5.65.5 12a11.5 11.5 0 0 0 7.87 10.93c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.54-3.88-1.54-.53-1.33-1.28-1.69-1.28-1.69-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.79 0c2.2-1.49 3.17-1.18 3.17-1.18.64 1.59.24 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.7 5.4-5.27 5.69.42.36.78 1.08.78 2.18v3.24c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z" />
  </svg>
);

export default LoginPage;