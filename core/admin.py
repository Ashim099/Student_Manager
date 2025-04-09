# core/admin.py
from django.contrib import admin
from .models import User, Program, Module, StudentProgram, Resource, Assignment, Submission, Result, Reminder, Announcement

admin.site.register(User)
admin.site.register(Program)
admin.site.register(Module)
admin.site.register(StudentProgram)
admin.site.register(Resource)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Result)
admin.site.register(Reminder)
admin.site.register(Announcement)