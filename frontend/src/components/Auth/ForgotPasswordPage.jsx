import { useState } from "react";
import { Mail } from "lucide-react";
import { CenteredAuthLayout } from "./AuthLayout";
import AuthField from "./AuthField";
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
    <CenteredAuthLayout
      icon={Mail}
      title="Forgot your password?"
      subtitle="No worries! Enter your email address and we'll send you a code to reset it."
      footer={
        <button type="button" onClick={() => onNavigate("login")} className="font-medium text-blue-600 hover:underline dark:text-blue-400">
          ← Back to login
        </button>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          label="Email address"
          icon={Mail}
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />

        {error ? <p className="text-sm text-red-500 dark:text-red-400">{error}</p> : null}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Sending…" : "Send reset code"}
        </button>
      </form>
    </CenteredAuthLayout>
  );
};

export default ForgotPasswordPage;