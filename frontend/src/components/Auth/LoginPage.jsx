import { useState } from "react";
import { LogIn } from "lucide-react";
import AuthLayout from "./AuthLayout";
import { authApi } from "../../services/authApi";
import { useAuth } from "../../context/AuthContext";

const LoginPage = ({ onNavigate }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
    <AuthLayout title="Welcome back" subtitle="Log in to continue">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-white/70">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-white/70">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="••••••••"
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple py-2 font-medium text-white transition hover:bg-brand-purple/90 disabled:opacity-60"
        >
          <LogIn className="h-4 w-4" />
          {loading ? "Logging in…" : "Log in"}
        </button>

        <div className="flex items-center justify-between text-sm">
          <button
            type="button"
            onClick={() => onNavigate("forgot-password")}
            className="text-brand-purple hover:underline"
          >
            Forgot password?
          </button>
          <button
            type="button"
            onClick={() => onNavigate("signup")}
            className="text-white/60 hover:underline"
          >
            Create account
          </button>
        </div>
      </form>
    </AuthLayout>
  );
};

export default LoginPage;