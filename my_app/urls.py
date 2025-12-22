from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('test/<int:test_id>/', views.take_test, name='take_test'),
    path('test/<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('results/<int:result_id>/', views.view_result, name='view_result'),
    
    # Custom admin panel
    path('custom-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/users/', views.admin_users, name='admin_users'),
    path('custom-admin/users/add/', views.admin_add_user, name='admin_add_user'),
    path('custom-admin/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    path('custom-admin/results/', views.admin_results, name='admin_results'),
    path('custom-admin/results/<int:user_id>/', views.admin_user_results, name='admin_user_results'),
    
    path('custom-admin/courses/', views.admin_courses, name='admin_courses'),
    path('custom-admin/courses/add/', views.admin_add_course, name='admin_add_course'),
    path('custom-admin/courses/<int:course_id>/edit/', views.admin_edit_course, name='admin_edit_course'),
    path('custom-admin/courses/<int:course_id>/delete/', views.admin_delete_course, name='admin_delete_course'),
    
    path('custom-admin/groups/', views.admin_groups, name='admin_groups'),
    path('custom-admin/groups/add/', views.admin_add_group, name='admin_add_group'),
    path('custom-admin/groups/<int:group_id>/edit/', views.admin_edit_group, name='admin_edit_group'),
    path('custom-admin/groups/<int:group_id>/delete/', views.admin_delete_group, name='admin_delete_group'),
    
    path('custom-admin/test-blocks/', views.admin_test_blocks, name='admin_test_blocks'),
    path('custom-admin/test-blocks/add/', views.admin_add_test_block, name='admin_add_test_block'),
    path('custom-admin/test-blocks/<int:block_id>/edit/', views.admin_edit_test_block, name='admin_edit_test_block'),
    path('custom-admin/test-blocks/<int:block_id>/delete/', views.admin_delete_test_block, name='admin_delete_test_block'),
    path('custom-admin/test-blocks/<int:block_id>/questions/', views.admin_test_questions, name='admin_test_questions'),
    path('custom-admin/test-blocks/<int:block_id>/questions/add/', views.admin_add_question, name='admin_add_question'),
    path('custom-admin/questions/<int:question_id>/edit/', views.admin_edit_question, name='admin_edit_question'),
    path('custom-admin/questions/<int:question_id>/delete/', views.admin_delete_question, name='admin_delete_question'),
]
