# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

class User(AbstractUser):
    ROLES = (('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin'))
    role = models.CharField(max_length=10, choices=ROLES, default='student')
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Program(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})

    def __str__(self):
        return self.name

class Module(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='modules')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                limit_choices_to={'role': 'teacher'}, related_name='modules_taught')

    def __str__(self):
        return f"{self.code} - {self.name}"

class StudentProgram(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'program')

    def __str__(self):
        return f"{self.student.username} - {self.program.name}"

class Resource(models.Model):
    title = models.CharField(max_length=100)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='resources')
    file = models.FileField(upload_to='resources/', 
                            validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'pptx'])])
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Assignment(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='assignments')
    file = models.FileField(upload_to='assignments/', null=True, blank=True, 
                            validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx'])])
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.module.code})"

class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='submissions/', 
                            validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx'])])
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'assignment')

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

class Result(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, 
                                limit_choices_to={'role': 'student'}, 
                                related_name='results_as_student')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='results')
    grade = models.FloatField()
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                    limit_choices_to={'role': 'teacher'}, 
                                    related_name='results_published')
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'module')

    def __str__(self):
        return f"{self.student.username} - {self.module.code}: {self.grade}"

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    message = models.CharField(max_length=200)
    datetime = models.DateTimeField()
    is_notified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.message}"

class Announcement(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='announcements')
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title