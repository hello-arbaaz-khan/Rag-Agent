import { useState } from "react";
import { Lock } from "lucide-react";
import AuthLayout from "./AuthLayout";
import { authApi } from "../../services/authApi";
import { useAuth } from "../../context/AuthContext";

// For a user who is ALREADY logged in and just wants to update their
// password. No OTP involved — their current password + a valid access
// token together prove identity. Unlike the other Auth/* pages, this one
// is meant to be rendered from inside the main authenticated app
// (e.g. a Settings/Account screen), not from the AuthPage switcher.
const ChangePasswordPage = ({ onDone }) => {
  const { tokens } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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
      setConfirmPassword("");
      onDone?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Change password" subtitle="Update the password on your account">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-white/70">Current password</label>
          <input
            type="password"
            required
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-brand-purple"
            placeholder="••••••••"
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
        {success && <p className="text-sm text-emerald-400">{success}</p>}

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-purple py-2 font-medium text-white transition hover:bg-brand-purple/90 disabled:opacity-60"
        >
          <Lock className="h-4 w-4" />
          {loading ? "Updating…" : "Change password"}
        </button>
      </form>
    </AuthLayout>
  );
};

export default ChangePasswordPage;