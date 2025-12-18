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
]
