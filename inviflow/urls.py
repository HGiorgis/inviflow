from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.core import views as core_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Main apps
    path('', include('apps.core.urls')),
    path('portfolio/', include('apps.portfolio.urls')),
    path('payments/', include('apps.payments.urls')),
    
    # ========== AUTHENTICATION ==========
    # Login - FIXED: Now redirects to dashboard after login
    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html',
        next_page='core:dashboard'  # This fixes the redirect to dashboard
    ), name='login'),
    
    # Logout
    path('logout/', auth_views.LogoutView.as_view(
        next_page='core:home'
    ), name='logout'),
    
    # Registration
    path('register/', core_views.RegisterView.as_view(), name='register'),
    
    # ========== PASSWORD MANAGEMENT ==========
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='auth/password_change.html',
        success_url='/password-change-done/'
    ), name='password_change'),
    
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/password_change_done.html'
    ), name='password_change_done'),
    
    # ========== API ENDPOINTS (FOR RENDER FREE TIER) ==========
    # Webhook for Google Sheets sync (no shell needed)
    path('api/sync-stocks/', core_views.webhook_sync_stocks, name='api_sync_stocks'),
    
    # Health check endpoint
    path('api/health/', core_views.health_check, name='api_health'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)