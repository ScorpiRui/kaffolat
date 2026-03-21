from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", csrf_exempt(auth_views.LoginView.as_view()), name="login"),
    path("accounts/logout/", csrf_exempt(auth_views.LogoutView.as_view()), name="logout"),
    path("", include("main.urls", namespace="main")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
