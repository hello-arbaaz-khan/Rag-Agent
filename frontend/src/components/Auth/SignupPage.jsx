import { useState, useEffect } from "react";
import {
  UserPlus,
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
} from "lucide-react";
import AuthLayout from "./AuthLayout";
import { authApi } from "../../services/authApi";

const passwordRequirements = [
  { regex: /.{8,}/, label: "At least 8 characters" },
  { regex: /[A-Z]/, label: "At least one uppercase letter" },
  { regex: /[a-z]/, label: "At least one lowercase letter" },
  { regex: /[0-9]/, label: "At least one number" },
  {
    regex: /[!@#$%^&*]/,
    label: "At least one special character (!@#$%^&*)",
  },
];

const isPasswordStrong = (pwd) =>
  passwordRequirements.every((req) => req.regex.test(pwd));

const SignupPage = ({ onNavigate }) => {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Clear form whenever SignupPage is mounted
  useEffect(() => {
    setDisplayName("");
    setEmail("");
    setPassword("");
    setShowPassword(false);
    setError("");
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await authApi.signup({
        email,
        password,
        displayName,
      });

      // Clear sensitive form data before leaving the page
      setPassword("");
      setEmail("");
      setDisplayName("");
      setShowPassword(false);

      onNavigate("verify-otp", { email });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="We'll email you a verification code"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Display Name */}
        <div>
          <label className="mb-1 block text-sm text-white/70">
            Display name
          </label>

          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="Display Name"
          />
        </div>

        {/* Email */}
        <div>
          <label className="mb-1 block text-sm text-white/70">
            Email
          </label>

          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="off"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="you@example.com"
          />
        </div>

        {/* Password */}
        <div>
          <label className="mb-1 block text-sm text-white/70">
            Password
          </label>

          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 pr-10 text-white outline-none focus:border-brand-purple"
              placeholder="Create a strong password"
            />

            {/* Show / Hide Password */}
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 transition hover:text-white"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          {/* Password Requirements */}
          {password && (
            <div className="mt-3 space-y-2 rounded-lg bg-white/5 p-3">
              {passwordRequirements.map((req, idx) => {
                const met = req.regex.test(password);

                return (
                  <div
                    key={idx}
                    className="flex items-center gap-2 text-xs"
                  >
                    {met ? (
                      <CheckCircle2 className="h-4 w-4 flex-shrink-0 text-emerald-400" />
                    ) : (
                      <AlertCircle className="h-4 w-4 flex-shrink-0 text-slate-400" />
                    )}

                    <span
                      className={
                        met ? "text-emerald-300" : "text-white/60"
                      }
                    >
                      {req.label}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Error */}
        {error && <p className="text-sm text-red-400">{error}</p>}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !isPasswordStrong(password)}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple py-2 font-medium text-white transition hover:bg-brand-purple/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <UserPlus className="h-4 w-4" />

          {loading ? "Creating account…" : "Sign up"}
        </button>

        {/* Login */}
        <p className="text-center text-sm text-white/60">
          Already have an account?{" "}
          <button
            type="button"
            onClick={() => onNavigate("login")}
            className="text-brand-purple hover:underline"
          >
            Log in
          </button>
        </p>
      </form>
    </AuthLayout>
  );
};

export default SignupPage;