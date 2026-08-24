import { useState } from "react";
import { Lock } from "lucide-react";
import AuthField from "./AuthField";
import { ShieldIllustration } from "./AuthIllustrations";
import { authApi } from "../../services/authApi";
import { useAuth } from "../../context/AuthContext";

// For a user who is ALREADY logged in and just wants to update their
// password. No OTP involved — their current password + a valid access
// token together prove identity. Rendered from inside the main authenticated
// app (Settings), so — unlike the other Auth/* pages — this is just the
// card, not a full-page shell with its own theme toggle / branding.
const ChangePasswordPage = ({ onDone }) => {
  const { tokens } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (newPassword === oldPassword) {
      setError("New password must be different from the old password.");
      return;
    }

    setLoading(true);
    try {
      await authApi.changePassword({
        oldPassword,
        newPassword,
        accessToken: tokens?.access
      });
      setSuccess("Password changed successfully.");
      setOldPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid w-full max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-slate-900/10 dark:border-white/10 dark:bg-brand-card lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-slate-900 via-[#0b0f19] to-indigo-950 p-10 text-white lg:flex">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(79,107,246,0.25),transparent_55%)]" />
        <div>
          <h2 className="text-2xl font-extrabold leading-tight">Change your password</h2>
          <p className="mt-3 max-w-xs text-sm leading-6 text-slate-300">
            Keep your account secure by using a strong and unique password you don&apos;t use anywhere else.
          </p>
        </div>
        <div className="relative flex-1">
          <ShieldIllustration />
        </div>
        <div />
      </div>

      <div className="p-8 sm:p-10">
        <div className="mx-auto w-full max-w-sm">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Change password</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Enter your current password and choose a new one.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <AuthField
              label="Current password"
              icon={Lock}
              type="password"
              required
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              placeholder="Enter current password"
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
            />
            <AuthField
              label="Confirm new password"
              icon={Lock}
              type="password"
              required
              minLength={8}
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              placeholder="Confirm new password"
            />

            {error ? <p className="text-sm text-red-500 dark:text-red-400">{error}</p> : null}
            {success ? <p className="text-sm text-emerald-600 dark:text-emerald-400">{success}</p> : null}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Updating…" : "Update password"}
            </button>

            {onDone ? (
              <button
                type="button"
                onClick={onDone}
                className="w-full text-center text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
              >
                ← Back to settings
              </button>
            ) : null}
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChangePasswordPage;