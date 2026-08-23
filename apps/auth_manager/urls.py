from django.urls import path
from apps.auth_manager import views

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("signup/verify-otp/", views.VerifySignupOTPView.as_view(), name="verify-signup-otp"),
    path("signup/resend-otp/", views.ResendOTPView.as_view(), name="resend-otp"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("password/forgot/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("password/reset/", views.ResetPasswordView.as_view(), name="reset-password"),
    path("password/change/", views.ChangePasswordView.as_view(), name="change-password"),
    path("verify-otp/", views.VerifyOtpGenericView.as_view(), name="verify-otp-generic"),
]