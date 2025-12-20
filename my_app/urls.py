from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('select-kurs/', views.select_kurs, name='select_kurs'),
    path('blocks/<int:kurs_id>/', views.blocks_list, name='blocks_list'),
    path('test/<int:block_id>/', views.start_test, name='start_test'),
    path('submit/<int:block_id>/', views.submit_test, name='submit_test'),
    path('result/<int:natija_id>/', views.test_result, name='test_result'),
    
    path('request-retest/<int:block_id>/', views.request_retest, name='request_retest'),
    
    # Admin routes
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('ad/approve-retest/<int:request_id>/', views.admin_approve_retest, name='admin_approve_retest'),
    path('ad/block-results/<int:block_id>/', views.admin_block_results, name='admin_block_results'),
]
