import { useState } from "react";
import { KeyRound } from "lucide-react";
import AuthLayout from "./AuthLayout";
import { authApi } from "../../services/authApi";

const ResetPasswordPage = ({ email: initialEmail, onNavigate }) => {
  const [email, setEmail] = useState(initialEmail || "");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await authApi.resetPassword({ email, otp, newPassword });
      // Backend invalidates the OTP on success and issues no tokens here —
      // the user logs in fresh with their new password.
      onNavigate("login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Reset password" subtitle="Enter the code we emailed you and choose a new password">
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
          <label className="mb-1 block text-sm text-white/70">OTP code</label>
          <input
            type="text"
            required
            inputMode="numeric"
            maxLength={4}
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-center text-lg tracking-[0.5em] text-white outline-none focus:border-brand-purple"
            placeholder="0000"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-white/70">New password</label>
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="At least 8 characters"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-white/70">Confirm new password</label>
          <input
            type="password"
            required
            minLength={8}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="Repeat new password"
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple py-2 font-medium text-white transition hover:bg-brand-purple/90 disabled:opacity-60"
        >
          <KeyRound className="h-4 w-4" />
          {loading ? "Resetting…" : "Reset password"}
        </button>

        <div className="flex items-center justify-between text-sm">
          <button
            type="button"
            onClick={() => onNavigate("forgot-password")}
            className="text-white/60 hover:underline"
          >
            Didn't get a code? Resend
          </button>
          <button type="button" onClick={() => onNavigate("login")} className="text-brand-purple hover:underline">
            Back to login
          </button>
        </div>
      </form>
    </AuthLayout>
  );
};

export default ResetPasswordPage;