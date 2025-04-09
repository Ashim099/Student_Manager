# core/serializers.py
from rest_framework import serializers
from core.models import User, Program, Module, StudentProgram, Resource, Assignment, Submission, Result, Reminder, Announcement

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = ['id', 'name', 'description', 'created_by']

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'code', 'name', 'program', 'teacher']

class StudentProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProgram
        fields = ['id', 'student', 'program', 'enrolled_at']

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'title', 'module', 'file', 'uploaded_by', 'uploaded_at']

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'module', 'file', 'due_date', 'created_by', 'created_at']

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'student', 'assignment', 'file', 'submitted_at', 'grade']

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'student', 'module', 'grade', 'published_by', 'published_at']

class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['id', 'user', 'message', 'datetime', 'is_notified']

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'module', 'posted_by', 'posted_at']