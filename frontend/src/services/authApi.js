import axios from "axios";

const AUTH_BASE_URL = "/api/auth/";

const authClient = axios.create({
  baseURL: AUTH_BASE_URL,
  timeout: 30000
});

const getErrorMessage = (error, fallback) => {
  const data = error?.response?.data;
  if (data?.message) return data.message;
  if (data?.errors) {
    return Object.entries(data.errors)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
      .join(" | ");
  }
  if (typeof data === "string") return data;
  if (error?.message) return error.message;
  return fallback;
};

export const authApi = {
  async signup({ email, password, displayName }) {
    try {
      const { data } = await authClient.post("signup/", {
        email,
        password,
        display_name: displayName
      });
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Signup failed."));
    }
  },

  async refreshAccessToken(refreshToken) {
  try {
    const { data } = await authClient.post("token/refresh/", { refresh: refreshToken });
    return data.data; // contains { access, refresh }
  } catch (error) {
    throw new Error(getErrorMessage(error, "Failed to refresh session."));
  }
},

  async verifySignupOtp({ email, otp }) {
    try {
      const { data } = await authClient.post("signup/verify-otp/", { email, otp });
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "OTP verification failed."));
    }
  },

  async resendOtp({ email }) {
    try {
      const { data } = await authClient.post("signup/resend-otp/", { email });
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Could not resend OTP."));
    }
  },

  async login({ email, password }) {
    try {
      const { data } = await authClient.post("login/", { email, password });
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Login failed."));
    }
  },

  async forgotPassword({ email }) {
    try {
      const { data } = await authClient.post("password/forgot/", { email });
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Could not send OTP."));
    }
  },

  async resetPassword({ email, otp, newPassword }) {
    try {
      const { data } = await authClient.post("password/reset/", {
        email,
        otp,
        new_password: newPassword
      });
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Password reset failed."));
    }
  },

  async changePassword({ oldPassword, newPassword, confirmNewPassword, accessToken }) {
    try {
      const { data } = await authClient.post(
        "password/change/",
        {
          old_password: oldPassword,
          new_password: newPassword,
          confirm_new_password: confirmNewPassword
        },
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      return data;
    } catch (error) {
      throw new Error(getErrorMessage(error, "Password change failed."));
    }
  }
};

export default authApi;