from django.urls import path
from accounts import views

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("signup/verify-otp/", views.VerifySignupOTPView.as_view(), name="verify-signup-otp"),
    path("signup/resend-otp/", views.ResendOTPView.as_view(), name="resend-otp"),
    path("login/", views.LoginView.as_view(), name="login"),
]