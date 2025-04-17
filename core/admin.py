from django.contrib import admin
from .models import User, Program, Module, StudentProgram, Resource, Assignment, Submission, Result, Reminder, Announcement

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'admin'

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_by']
    search_fields = ['name']
    list_filter = ['created_by']

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'program', 'teacher']
    search_fields = ['code', 'name']
    list_filter = ['program']

@admin.register(StudentProgram)
class StudentProgramAdmin(admin.ModelAdmin):
    list_display = ['student', 'program']
    list_filter = ['program']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'uploaded_by', 'uploaded_at']
    list_filter = ['module', 'uploaded_at']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'due_date', 'created_by']
    list_filter = ['module', 'due_date']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'student', 'submitted_at']
    list_filter = ['assignment', 'submitted_at']

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'module', 'grade']
    list_filter = ['module']

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'reminder_date']
    list_filter = ['reminder_date']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'created_by', 'created_at']
    list_filter = ['module', 'created_at']