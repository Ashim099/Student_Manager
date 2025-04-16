from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.sites import AdminSite
from django.shortcuts import redirect 

class CustomAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        # Redirect to /admin/dashboard/ after login
        if request.method == 'POST' and request.user.is_authenticated:
            return redirect('admin_dashboard')
        return super().login(request, extra_context)

admin.site = CustomAdminSite(name='custom_admin')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)