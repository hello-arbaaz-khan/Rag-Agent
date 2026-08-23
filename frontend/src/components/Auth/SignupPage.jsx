import { useState } from "react";
import { UserPlus } from "lucide-react";
import AuthLayout from "./AuthLayout";
import { authApi } from "../../services/authApi";

const SignupPage = ({ onNavigate }) => {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.signup({ email, password, displayName });
      // Signup only creates an inactive user + sends an OTP — the account
      // isn't usable until VerifySignupOTPView activates it.
      onNavigate("verify-otp", { email });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create your account" subtitle="We'll email you a verification code">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-white/70">Display name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="Jane Doe"
          />
        </div>
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
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="At least 8 characters"
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple py-2 font-medium text-white transition hover:bg-brand-purple/90 disabled:opacity-60"
        >
          <UserPlus className="h-4 w-4" />
          {loading ? "Creating account…" : "Sign up"}
        </button>

        <p className="text-center text-sm text-white/60">
          Already have an account?{" "}
          <button type="button" onClick={() => onNavigate("login")} className="text-brand-purple hover:underline">
            Log in
          </button>
        </p>
      </form>
    </AuthLayout>
  );
};

export default SignupPage;