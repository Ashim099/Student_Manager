from django.urls import path
from .views import (
    homepage_view, signup_view, verify_otp_signup, login_view, student_login, teacher_login, admin_login,
    verify_otp, logout_view, admin_dashboard_view, admin_create_program, admin_create_module, admin_assign_teacher,
    admin_enroll_student, teacher_dashboard_view, teacher_manage_resources, teacher_delete_resource,
    teacher_share_assignment, teacher_post_announcement, teacher_publish_result, student_dashboard_view,
    student_choose_program, student_pomodoro_timer, student_set_reminder, student_submit_assignment
)

# student_gpa_prediction, student_course_recommendation

urlpatterns = [
    path('', homepage_view, name='homepage'),
    path('signup/', signup_view, name='signup'),
    path('verify-otp-signup/', verify_otp_signup, name='verify_otp_signup'),
    path('login/', login_view, name='login'),
    path('student-login/', student_login, name='student_login'),
    path('teacher-login/', teacher_login, name='teacher_login'),
    path('admin-login/', admin_login, name='admin_login'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('logout/', logout_view, name='logout'),
    path('admin/dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('admin/create-program/', admin_create_program, name='admin_create_program'),
    path('admin/create-module/', admin_create_module, name='admin_create_module'),
    path('admin/assign-teacher/<int:module_id>/', admin_assign_teacher, name='admin_assign_teacher'),
    path('admin/enroll-student/<int:program_id>/', admin_enroll_student, name='admin_enroll_student'),
    path('teacher/dashboard/', teacher_dashboard_view, name='teacher_dashboard'),
    path('teacher/manage-resources/<int:module_id>/', teacher_manage_resources, name='teacher_manage_resources'),
    path('teacher/delete-resource/<int:resource_id>/', teacher_delete_resource, name='teacher_delete_resource'),
    path('teacher/share-assignment/<int:module_id>/', teacher_share_assignment, name='teacher_share_assignment'),
    path('teacher/post-announcement/<int:module_id>/', teacher_post_announcement, name='teacher_post_announcement'),
    path('teacher/publish-result/<int:module_id>/', teacher_publish_result, name='teacher_publish_result'),
    path('student/dashboard/', student_dashboard_view, name='student_dashboard'),
    path('student/choose-program/', student_choose_program, name='student_choose_program'),
    path('student/pomodoro-timer/', student_pomodoro_timer, name='student_pomodoro_timer'),
    path('student/set-reminder/', student_set_reminder, name='student_set_reminder'),
    path('student/submit-assignment/<int:assignment_id>/', student_submit_assignment, name='student_submit_assignment'),
    # Uncomment these paths when ML models are implemented
    # path('student/gpa-prediction/', student_gpa_prediction, name='student_gpa_prediction'),
    # path('student/course-recommendation/', student_course_recommendation, name='student_course_recommendation'),
]