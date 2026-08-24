import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { CenteredAuthLayout } from "./AuthLayout";
import { authApi } from "../../services/authApi";
import { useAuth } from "../../context/AuthContext";

// Mirrors the backend's default OTP_EXPIRY_SECONDS (see apps/auth_manager/utils.py).
// Only used to disable the "resend" button for a moment — the backend is the
// source of truth for actual expiry.
const OTP_COOLDOWN_SECONDS = 30;

const VerifyOtpPage = ({ email, onNavigate }) => {
  const { login } = useAuth();
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(OTP_COOLDOWN_SECONDS);

  useEffect(() => {
    if (cooldown <= 0) return undefined;
    const timer = window.setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [cooldown]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      const res = await authApi.verifySignupOtp({ email, otp });
      login(res.data.user, res.data.tokens);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setInfo("");
    try {
      await authApi.resendOtp({ email });
      setInfo("A new code has been sent to your email.");
      setCooldown(OTP_COOLDOWN_SECONDS);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!email) {
    return (
      <CenteredAuthLayout icon={ShieldCheck} title="Verify your email">
        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          Missing email context.{" "}
          <button type="button" onClick={() => onNavigate("signup")} className="font-medium text-blue-600 hover:underline dark:text-blue-400">
            Start signup again
          </button>
          .
        </p>
      </CenteredAuthLayout>
    );
  }

  return (
    <CenteredAuthLayout
      icon={ShieldCheck}
      title="Verify your email"
      subtitle={`Enter the 4-digit code we sent to ${email}`}
      footer={
        <button
          type="button"
          onClick={handleResend}
          disabled={cooldown > 0}
          className="font-medium text-blue-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-400 disabled:no-underline dark:text-blue-400 dark:disabled:text-slate-500"
        >
          {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend code"}
        </button>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Verification code</span>
          <input
            type="text"
            required
            inputMode="numeric"
            maxLength={4}
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-center text-lg font-semibold tracking-[0.5em] text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500/15 dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:focus:bg-white/[0.06]"
            placeholder="0000"
          />
        </label>

        {error ? <p className="text-sm text-red-500 dark:text-red-400">{error}</p> : null}
        {info ? <p className="text-sm text-emerald-600 dark:text-emerald-400">{info}</p> : null}

        <button
          type="submit"
          disabled={loading || otp.length !== 4}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <ShieldCheck className="h-4 w-4" />
          {loading ? "Verifying…" : "Verify"}
        </button>
      </form>
    </CenteredAuthLayout>
  );
};

export default VerifyOtpPage;