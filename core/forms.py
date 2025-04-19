from django import forms
from .models import User, Resource, Assignment, Announcement

class AdminAddUserForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('student', 'Student'), ('teacher', 'Teacher')], label="Role")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    class Meta:
        model = User
        fields = ['email', 'username', 'role', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_active = True  # Activate user immediately
        if commit:
            user.save()
        return user
    
class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'file', 'module']
        widgets = {
            'module': forms.HiddenInput(),
        }

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'module']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'module': forms.HiddenInput(),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'file', 'module']
        widgets = {
            'module': forms.HiddenInput(),
        }