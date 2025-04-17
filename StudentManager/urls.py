from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.sites import AdminSite
from django.shortcuts import redirect
from django.contrib import messages
import logging

# Set up logging to debug redirect issues
logger = logging.getLogger(__name__)

class CustomAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        logger.info(f"Admin login attempt: user={request.user}, authenticated={request.user.is_authenticated}")
        return super().login(request, extra_context)

    def each_context(self, request):
        context = super().each_context(request)
        # Redirect to admin_dashboard after login
        if request.user.is_authenticated:
            logger.info(f"User authenticated: is_superuser={request.user.is_superuser}, role={request.user.role}")
            if request.user.is_superuser or request.user.role == 'admin':
                # Avoid redirect loop by checking if we're on the login page
                if request.path == self.login_url or request.path == '/admin/':
                    logger.info("Redirecting to admin_dashboard")
                    return redirect('admin_dashboard')
            else:
                logger.info("User lacks permission, redirecting to homepage")
                messages.error(request, 'You do not have permission to access the admin dashboard.')
                return redirect('homepage')
        return context

    def has_permission(self, request):
        # Allow access to /admin/ for superusers or users with role='admin'
        has_perm = request.user.is_active and (request.user.is_superuser or request.user.role == 'admin')
        logger.info(f"has_permission check: user={request.user}, result={has_perm}")
        return has_perm

admin.site = CustomAdminSite(name='custom_admin')

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)