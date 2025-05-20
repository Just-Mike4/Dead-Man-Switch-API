"""
URL configuration for dms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from user.views import RegisterationViewSet, LoginViewSet,PasswordResetView,PasswordResetConfirmView
from switch.views import SwitchViewSet, ActionViewSet, webhook_test,UserStatusView

router= DefaultRouter()

router.register(r"register", RegisterationViewSet, basename="register")
router.register(r"login", LoginViewSet, basename="login")
router.register(r'switches', SwitchViewSet, basename='switch')
router.register(r'actions', ActionViewSet, basename='action')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path('api/webhook-test/', webhook_test),
    path('api/my-status/', UserStatusView.as_view()),
    path('api/password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('api/password-reset-confirm/<uid>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
