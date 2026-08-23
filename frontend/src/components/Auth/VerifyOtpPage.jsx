import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import AuthLayout from "./AuthLayout";
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
      setInfo("A new OTP has been sent to your email.");
      setCooldown(OTP_COOLDOWN_SECONDS);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!email) {
    return (
      <AuthLayout title="Verify your email">
        <p className="text-sm text-white/70">
          Missing email context.{" "}
          <button type="button" onClick={() => onNavigate("signup")} className="text-brand-purple hover:underline">
            Start signup again
          </button>
          .
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Verify your email" subtitle={`Enter the code sent to ${email}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
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

        {error && <p className="text-sm text-red-400">{error}</p>}
        {info && <p className="text-sm text-emerald-400">{info}</p>}

        <button
          type="submit"
          disabled={loading || otp.length !== 4}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple py-2 font-medium text-white transition hover:bg-brand-purple/90 disabled:opacity-60"
        >
          <ShieldCheck className="h-4 w-4" />
          {loading ? "Verifying…" : "Verify"}
        </button>

        <button
          type="button"
          onClick={handleResend}
          disabled={cooldown > 0}
          className="w-full text-center text-sm text-white/60 hover:underline disabled:cursor-not-allowed disabled:text-white/30"
        >
          {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend code"}
        </button>
      </form>
    </AuthLayout>
  );
};

export default VerifyOtpPage;