from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.CustomLoginView.as_view(), name='login'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Student Management
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/add/', views.StudentCreateView.as_view(), name='student_add'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('students/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('students/<int:pk>/detail/', views.StudentDetailView.as_view(), name='student_detail'),

    # Attendance Management
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),
    path('attendance/mark/', views.MarkAttendanceView.as_view(), name='mark_attendance'),
    path('attendance/bulk/', views.BulkAttendanceView.as_view(), name='bulk_attendance'),
    path('attendance/<int:pk>/edit/', views.AttendanceUpdateView.as_view(), name='attendance_edit'),

    # Fee Management
    path('fees/', views.FeeTransactionListView.as_view(), name='fee_list'),
    path('fees/add/', views.FeeTransactionCreateView.as_view(), name='fee_add'),
    path('fees/<int:pk>/edit/', views.FeeTransactionUpdateView.as_view(), name='fee_edit'),
    path('fees/<int:pk>/delete/', views.FeeTransactionDeleteView.as_view(), name='fee_delete'),

    # Analytics & Reports
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('reports/attendance/', views.AttendanceReportView.as_view(), name='attendance_report'),
    path('reports/fees/', views.FeeReportView.as_view(), name='fee_report'),
    path('export/attendance/', views.ExportAttendanceView.as_view(), name='export_attendance'),
    path('export/fees/', views.ExportFeesView.as_view(), name='export_fees'),

    # Admin User Management
    path('admin-users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin-users/add/', views.AdminUserCreateView.as_view(), name='admin_user_add'),
    path('admin-users/<int:pk>/edit/', views.AdminUserUpdateView.as_view(), name='admin_user_edit'),
    path('admin-users/<int:pk>/delete/', views.AdminUserDeleteView.as_view(), name='admin_user_delete'),

    # Fee Configuration
    path('config/fees/', views.FeeConfigurationView.as_view(), name='fee_config'),

    # API endpoints for AJAX calls
    path('api/students/search/', views.StudentSearchAPIView.as_view(), name='api_student_search'),
    path('api/attendance/chart/', views.AttendanceChartAPIView.as_view(), name='api_attendance_chart'),
    path('api/fee/chart/', views.FeeChartAPIView.as_view(), name='api_fee_chart'),
    path('api/dashboard/stats/', views.DashboardStatsAPIView.as_view(), name='api_dashboard_stats'),
]
