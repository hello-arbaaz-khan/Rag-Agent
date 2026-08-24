import { useState } from "react";
import { KeyRound, Lock, Mail } from "lucide-react";
import { SplitAuthLayout } from "./AuthLayout";
import AuthField from "./AuthField";
import { ShieldIllustration } from "./AuthIllustrations";
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
    <SplitAuthLayout
      title="Reset your"
      highlight="password."
      description="Enter your new password below to regain access to your account. Make it strong and memorable."
      illustration={<ShieldIllustration variant="lock" />}
      formTitle="Set new password"
      formSubtitle="Your new password must be at least 8 characters and include a mix of letters, numbers and symbols."
      footer={
        <button type="button" onClick={() => onNavigate("login")} className="font-medium text-blue-600 hover:underline dark:text-blue-400">
          ← Back to login
        </button>
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
          name="reset-email"
          autoComplete="off"
        />
        <AuthField
          label="Verification code"
          icon={KeyRound}
          type="text"
          required
          inputMode="numeric"
          maxLength={4}
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
          placeholder="Enter the 4-digit code we emailed you"
          name="reset-otp"
          autoComplete="off"
        />
        <AuthField
          label="New password"
          icon={Lock}
          type="password"
          required
          minLength={8}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          placeholder="Enter new password"
          name="reset-new-password"
          autoComplete="new-password"
        />
        <AuthField
          label="Confirm password"
          icon={Lock}
          type="password"
          required
          minLength={8}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm your password"
          name="reset-confirm-password"
          autoComplete="new-password"
        />

        {error ? <p className="text-sm text-red-500 dark:text-red-400">{error}</p> : null}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Resetting…" : "Reset password"}
        </button>

        <button
          type="button"
          onClick={() => onNavigate("forgot-password")}
          className="w-full text-center text-sm text-slate-500 hover:underline dark:text-slate-400"
        >
          Didn&apos;t get a code? Resend
        </button>
      </form>
    </SplitAuthLayout>
  );
};

export default ResetPasswordPage;