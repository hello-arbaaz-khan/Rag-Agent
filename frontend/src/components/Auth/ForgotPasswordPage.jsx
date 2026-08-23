import { useState } from "react";
import { Mail } from "lucide-react";
import AuthLayout from "./AuthLayout";
import { authApi } from "../../services/authApi";

const ForgotPasswordPage = ({ onNavigate }) => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      // Backend always responds with a generic success message here
      // (even for unknown emails) so this can't be used to enumerate accounts.
      await authApi.forgotPassword({ email });
      onNavigate("reset-password", { email });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Forgot password" subtitle="We'll email you a one-time code">
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

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple py-2 font-medium text-white transition hover:bg-brand-purple/90 disabled:opacity-60"
        >
          <Mail className="h-4 w-4" />
          {loading ? "Sending…" : "Send OTP"}
        </button>

        <p className="text-center text-sm text-white/60">
          Remembered it?{" "}
          <button type="button" onClick={() => onNavigate("login")} className="text-brand-purple hover:underline">
            Back to login
          </button>
        </p>
      </form>
    </AuthLayout>
  );
};

export default ForgotPasswordPage;