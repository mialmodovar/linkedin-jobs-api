from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.index, name='index'),
    path('queries/', views.query_list, name='query_list'),
    path('queries/create/', views.query_create, name='query_create'),
    path('queries/<int:pk>/', views.query_detail, name='query_detail'),
    path('queries/<int:pk>/edit/', views.query_edit, name='query_edit'),
    path('queries/<int:pk>/delete/', views.query_delete, name='query_delete'),
    path('queries/<int:pk>/toggle/', views.query_toggle, name='query_toggle'),
    path('queries/<int:pk>/run/', views.run_query_now, name='run_query_now'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/fetch-details/', views.fetch_job_details_now, name='fetch_job_details_now'),
    path('jobs/<int:pk>/check-status/', views.check_fetch_status, name='check_fetch_status'),
]
