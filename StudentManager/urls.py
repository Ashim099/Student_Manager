from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.sites import AdminSite
from django.shortcuts import redirect
from django.contrib import messages

class CustomAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        if request.method == 'POST' and request.user.is_authenticated:
            # Allow superusers or users with role='admin' to access the dashboard
            if request.user.is_superuser or request.user.role == 'admin':
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'You do not have permission to access the admin dashboard.')
                return redirect('homepage')
        return super().login(request, extra_context)

    def has_permission(self, request):
        return request.user.is_active and (request.user.is_superuser or request.user.role == 'admin')

admin.site = CustomAdminSite(name='custom_admin')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)