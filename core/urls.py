# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (UserViewSet, ProgramViewSet, ModuleViewSet, StudentProgramViewSet,
                    ResourceViewSet, AssignmentViewSet, SubmissionViewSet,
                    ResultViewSet, ReminderViewSet, AnnouncementViewSet,
                    homepage_view, login_view, student_dashboard_view,
                    teacher_dashboard_view, admin_dashboard_view, logout_view)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'programs', ProgramViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'student-programs', StudentProgramViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'submissions', SubmissionViewSet)
router.register(r'results', ResultViewSet)
router.register(r'reminders', ReminderViewSet)
router.register(r'announcements', AnnouncementViewSet)

urlpatterns = [
    path('', homepage_view, name='homepage'),
    path('api/', include(router.urls)),
    path('login/', login_view, name='login'),
    path('student/dashboard/', student_dashboard_view, name='student_dashboard'),
    path('teacher/dashboard/', teacher_dashboard_view, name='teacher_dashboard'),
    path('admin/dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('logout/', logout_view, name='logout'),
]