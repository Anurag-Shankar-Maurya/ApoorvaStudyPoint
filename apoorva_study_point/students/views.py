from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView,
    DetailView, FormView, TemplateView
)
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from .models import Student, Attendance, FeeTransaction, FeeConfiguration, UserProfile, Shift
from .forms import (
    StudentForm, AttendanceForm, BulkAttendanceForm, FeeTransactionForm,
    FeeConfigurationForm, CustomUserCreationForm, StudentSearchForm,
    AttendanceFilterForm, FeeTransactionFilterForm
)

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is admin or super admin"""
    def test_func(self):
        try:
            return self.request.user.profile.is_admin
        except:
            return self.request.user.is_superuser

class SuperAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is super admin"""
    def test_func(self):
        try:
            return self.request.user.profile.is_super_admin
        except:
            return self.request.user.is_superuser

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard')

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)

class DashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate dashboard statistics
        total_students = Student.objects.filter(is_active=True).count()

        # Total revenue collected
        total_revenue = FeeTransaction.objects.filter(
            payment_status='COMPLETED'
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

        # Total pending fees
        total_pending = Student.objects.filter(
            is_active=True
        ).aggregate(total=Sum('total_due_amount'))['total'] or Decimal('0.00')

        context.update({
            'total_students': total_students,
            'total_revenue': total_revenue,
            'total_pending': total_pending,
        })

        return context

class StudentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        queryset = Student.objects.filter(is_active=True).prefetch_related('enrolled_shifts')

        # Apply search and filters
        search_form = StudentSearchForm(self.request.GET)
        if search_form.is_valid():
            search_query = search_form.cleaned_data.get('search_query')
            shift_filter = search_form.cleaned_data.get('shift_filter')
            fee_status_filter = search_form.cleaned_data.get('fee_status_filter')

            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(contact__icontains=search_query)
                )

            if shift_filter:
                queryset = queryset.filter(enrolled_shifts=shift_filter)

            if fee_status_filter:
                queryset = queryset.filter(fee_status=fee_status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = StudentSearchForm(self.request.GET)
        return context

class StudentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/add_student.html'
    success_url = reverse_lazy('student_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Calculate and update fees
        self.object.calculate_total_fee()
        self.object.update_fee_status()
        messages.success(self.request, f'Student {self.object.name} added successfully!')
        return response

class StudentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/add_student.html'
    success_url = reverse_lazy('student_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Recalculate fees
        self.object.calculate_total_fee()
        self.object.update_fee_status()
        messages.success(self.request, f'Student {self.object.name} updated successfully!')
        return response

class StudentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Student
    template_name = 'students/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Soft delete
        self.object.is_active = False
        self.object.save()
        messages.success(request, f'Student {self.object.name} deleted successfully!')
        return redirect(self.success_url)

class StudentDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        # Get recent attendance records
        recent_attendance = student.attendance_records.order_by('-date')[:10]

        # Get recent fee transactions
        recent_transactions = student.fee_transactions.order_by('-payment_date')[:10]

        # Calculate attendance statistics
        total_attendance = student.attendance_records.count()
        present_count = student.attendance_records.filter(status='PRESENT').count()
        attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0

        context.update({
            'recent_attendance': recent_attendance,
            'recent_transactions': recent_transactions,
            'attendance_percentage': round(attendance_percentage, 2),
            'total_paid': student.get_total_paid(),
            'remaining_due': student.get_remaining_due(),
        })

        return context

class AttendanceListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Attendance
    template_name = 'attendance/attendance.html'
    context_object_name = 'attendance_records'
    paginate_by = 50

    def get_queryset(self):
        queryset = Attendance.objects.select_related('student', 'shift', 'marked_by')

        # Apply filters
        filter_form = AttendanceFilterForm(self.request.GET)
        if filter_form.is_valid():
            date_from = filter_form.cleaned_data.get('date_from')
            date_to = filter_form.cleaned_data.get('date_to')
            shift_filter = filter_form.cleaned_data.get('shift_filter')
            student_filter = filter_form.cleaned_data.get('student_filter')

            if date_from:
                queryset = queryset.filter(date__gte=date_from)
            if date_to:
                queryset = queryset.filter(date__lte=date_to)
            if shift_filter:
                queryset = queryset.filter(shift=shift_filter)
            if student_filter:
                queryset = queryset.filter(student=student_filter)

        return queryset.order_by('-date', 'shift', 'student')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = AttendanceFilterForm(self.request.GET)
        context['shifts'] = Shift.objects.filter(is_active=True)
        return context

class MarkAttendanceView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    template_name = 'attendance/mark_attendance.html'
    form_class = AttendanceForm
    success_url = reverse_lazy('attendance_list')

    def form_valid(self, form):
        attendance = form.save(commit=False)
        attendance.marked_by = self.request.user
        attendance.save()
        messages.success(self.request, 'Attendance marked successfully!')
        return super().form_valid(form)

class BulkAttendanceView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    template_name = 'attendance/bulk_attendance.html'

    def get_form_class(self):
        return BulkAttendanceForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        date_str = self.request.GET.get('date', date.today().strftime('%Y-%m-%d'))
        shift_id = self.request.GET.get('shift')

        if shift_id:
            try:
                shift = Shift.objects.get(id=shift_id)
                # Get students enrolled in this shift
                students = Student.objects.filter(
                    enrolled_shifts=shift,
                    is_active=True
                ).order_by('name')
                kwargs['students'] = students
            except Shift.DoesNotExist:
                kwargs['students'] = []
        else:
            kwargs['students'] = []

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shifts'] = Shift.objects.filter(is_active=True)
        context['selected_date'] = self.request.GET.get('date', date.today().strftime('%Y-%m-%d'))
        context['selected_shift'] = self.request.GET.get('shift')
        return context

    def form_valid(self, form):
        attendance_date = form.cleaned_data['date']
        shift = form.cleaned_data['shift']

        # Process bulk attendance
        created_count = 0
        for field_name, status in form.cleaned_data.items():
            if field_name.startswith('student_'):
                student_id = field_name.split('_')[1]
                try:
                    student = Student.objects.get(id=student_id)
                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        shift=shift,
                        date=attendance_date,
                        defaults={
                            'status': status,
                            'marked_by': self.request.user
                        }
                    )
                    if not created:
                        attendance.status = status
                        attendance.marked_by = self.request.user
                        attendance.save()
                    created_count += 1
                except Student.DoesNotExist:
                    continue

        messages.success(self.request, f'Attendance marked for {created_count} students!')
        return redirect('attendance_list')

class AttendanceUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/edit_attendance.html'
    success_url = reverse_lazy('attendance_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Attendance updated successfully!')
        return response

class FeeTransactionListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = FeeTransaction
    template_name = 'fees/fee_management.html'
    context_object_name = 'transactions'
    paginate_by = 50

    def get_queryset(self):
        queryset = FeeTransaction.objects.select_related('student', 'processed_by')

        # Apply filters
        filter_form = FeeTransactionFilterForm(self.request.GET)
        if filter_form.is_valid():
            status_filter = filter_form.cleaned_data.get('status_filter')
            month_filter = filter_form.cleaned_data.get('month_filter')
            shift_filter = filter_form.cleaned_data.get('shift_filter')

            if status_filter:
                queryset = queryset.filter(payment_status=status_filter)
            if month_filter:
                year, month = month_filter.split('-')
                queryset = queryset.filter(
                    payment_date__year=year,
                    payment_date__month=month
                )
            if shift_filter:
                queryset = queryset.filter(student__enrolled_shifts=shift_filter)

        return queryset.order_by('-payment_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = FeeTransactionFilterForm(self.request.GET)
        return context

class FeeTransactionCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = FeeTransaction
    form_class = FeeTransactionForm
    template_name = 'fees/add_fee_transaction.html'
    success_url = reverse_lazy('fee_list')

    def form_valid(self, form):
        transaction = form.save(commit=False)
        transaction.processed_by = self.request.user

        # Calculate remaining due after this payment
        student = transaction.student
        current_due = student.get_remaining_due()
        transaction.remaining_due_after_payment = max(
            Decimal('0.00'), 
            current_due - transaction.amount_paid
        )

        transaction.save()
        messages.success(self.request, f'Fee payment of ₹{transaction.amount_paid} recorded successfully!')
        return super().form_valid(form)

class FeeTransactionUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = FeeTransaction
    form_class = FeeTransactionForm
    template_name = 'fees/add_fee_transaction.html'
    success_url = reverse_lazy('fee_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Fee transaction updated successfully!')
        return response

class FeeTransactionDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = FeeTransaction
    template_name = 'fees/fee_transaction_confirm_delete.html'
    success_url = reverse_lazy('fee_list')

    def delete(self, request, *args, **kwargs):
        transaction = self.get_object()
        student = transaction.student
        response = super().delete(request, *args, **kwargs)

        # Update student's fee status after deletion
        student.update_fee_status()
        messages.success(request, 'Fee transaction deleted successfully!')
        return response

class AnalyticsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'analytics/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Student attendance summary
        attendance_summary = []
        for student in Student.objects.filter(is_active=True):
            total_recorded = student.attendance_records.count()
            total_present = student.attendance_records.filter(status='PRESENT').count()
            attendance_percentage = (total_present / total_recorded * 100) if total_recorded > 0 else 0

            attendance_summary.append({
                'student': student,
                'recorded_shifts': total_recorded,
                'present_shifts': total_present,
                'attendance_percentage': round(attendance_percentage, 2)
            })

        # Student fee summary
        fee_summary = []
        for student in Student.objects.filter(is_active=True):
            total_paid = student.get_total_paid()
            current_due = student.get_remaining_due()

            fee_summary.append({
                'student': student,
                'total_paid': total_paid,
                'current_due': current_due,
                'status': student.fee_status
            })

        context.update({
            'attendance_summary': attendance_summary,
            'fee_summary': fee_summary,
        })

        return context

class AttendanceReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'analytics/attendance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Generate detailed attendance report
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if date_from and date_to:
            attendance_data = Attendance.objects.filter(
                date__range=[date_from, date_to]
            ).select_related('student', 'shift')
        else:
            # Default to current month
            today = date.today()
            first_day = today.replace(day=1)
            attendance_data = Attendance.objects.filter(
                date__gte=first_day
            ).select_related('student', 'shift')

        context['attendance_data'] = attendance_data
        context['date_from'] = date_from
        context['date_to'] = date_to

        return context

class FeeReportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'analytics/fee_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Generate detailed fee report
        month_filter = self.request.GET.get('month')

        if month_filter:
            year, month = month_filter.split('-')
            transactions = FeeTransaction.objects.filter(
                payment_date__year=year,
                payment_date__month=month
            ).select_related('student', 'processed_by')
        else:
            # Default to current month
            today = date.today()
            transactions = FeeTransaction.objects.filter(
                payment_date__year=today.year,
                payment_date__month=today.month
            ).select_related('student', 'processed_by')

        context['transactions'] = transactions
        context['month_filter'] = month_filter

        return context

class AdminUserListView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    model = User
    template_name = 'admin_management/user_management.html'
    context_object_name = 'admin_users'

    def get_queryset(self):
        return User.objects.filter(
            profile__isnull=False,
            is_active=True
        ).select_related('profile').exclude(id=self.request.user.id)

class AdminUserCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, CreateView):
    form_class = CustomUserCreationForm
    template_name = 'admin_management/add_admin_user.html'
    success_url = reverse_lazy('admin_user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Set created_by for the profile
        self.object.profile.created_by = self.request.user
        self.object.profile.save()
        messages.success(self.request, f'Admin user {self.object.username} created successfully!')
        return response

class AdminUserUpdateView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
    template_name = 'admin_management/edit_admin_user.html'
    success_url = reverse_lazy('admin_user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Admin user {self.object.username} updated successfully!')
        return response

class AdminUserDeleteView(LoginRequiredMixin, SuperAdminRequiredMixin, DeleteView):
    model = User
    template_name = 'admin_management/admin_user_confirm_delete.html'
    success_url = reverse_lazy('admin_user_list')

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        # Soft delete
        user.is_active = False
        user.save()
        messages.success(request, f'Admin user {user.username} deactivated successfully!')
        return redirect(self.success_url)

class FeeConfigurationView(LoginRequiredMixin, SuperAdminRequiredMixin, FormView):
    form_class = FeeConfigurationForm
    template_name = 'config/fee_config.html'
    success_url = reverse_lazy('fee_config')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = FeeConfiguration.get_instance()
        return kwargs

    def form_valid(self, form):
        config = form.save(commit=False)
        config.updated_by = self.request.user
        config.save()

        # Update all students' fees based on new configuration
        for student in Student.objects.filter(is_active=True):
            student.calculate_total_fee()
            student.update_fee_status()

        messages.success(self.request, 'Fee configuration updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = FeeConfiguration.get_instance()
        return context

# API Views for AJAX calls
class StudentSearchAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        students = Student.objects.filter(
            Q(name__icontains=query) | Q(contact__icontains=query),
            is_active=True
        )[:10]

        results = []
        for student in students:
            results.append({
                'id': student.id,
                'name': student.name,
                'contact': student.contact,
                'due_amount': str(student.get_remaining_due())
            })

        return JsonResponse({'results': results})

class AttendanceChartAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        # Generate attendance chart data
        period = request.GET.get('period', 'month')

        if period == 'month':
            # Last 30 days
            start_date = date.today() - timedelta(days=30)
            attendance_data = Attendance.objects.filter(
                date__gte=start_date
            ).values('date').annotate(
                present=Count('id', filter=Q(status='PRESENT')),
                absent=Count('id', filter=Q(status='ABSENT'))
            ).order_by('date')

        chart_data = {
            'labels': [item['date'].strftime('%Y-%m-%d') for item in attendance_data],
            'present': [item['present'] for item in attendance_data],
            'absent': [item['absent'] for item in attendance_data]
        }

        return JsonResponse(chart_data)

class FeeChartAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        # Generate fee collection chart data
        period = request.GET.get('period', 'month')

        if period == 'month':
            # Last 12 months
            chart_data = []
            for i in range(12):
                month_date = date.today().replace(day=1) - timedelta(days=30*i)
                monthly_collection = FeeTransaction.objects.filter(
                    payment_date__year=month_date.year,
                    payment_date__month=month_date.month,
                    payment_status='COMPLETED'
                ).aggregate(total=Sum('amount_paid'))['total'] or 0

                chart_data.append({
                    'month': month_date.strftime('%Y-%m'),
                    'collection': float(monthly_collection)
                })

        return JsonResponse({'data': list(reversed(chart_data))})

class DashboardStatsAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        # Real-time dashboard statistics
        stats = {
            'total_students': Student.objects.filter(is_active=True).count(),
            'total_revenue': float(FeeTransaction.objects.filter(
                payment_status='COMPLETED'
            ).aggregate(total=Sum('amount_paid'))['total'] or 0),
            'total_pending': float(Student.objects.filter(
                is_active=True
            ).aggregate(total=Sum('total_due_amount'))['total'] or 0),
            'today_attendance': Attendance.objects.filter(
                date=date.today()
            ).count(),
        }

        return JsonResponse(stats)

class ExportAttendanceView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        # Export attendance data to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Student Name', 'Shift', 'Status', 'Marked By'])

        # Get filtered attendance data
        attendance_records = Attendance.objects.select_related(
            'student', 'shift', 'marked_by'
        ).order_by('-date')

        for record in attendance_records:
            writer.writerow([
                record.date,
                record.student.name,
                record.shift.get_name_display(),
                record.get_status_display(),
                record.marked_by.username if record.marked_by else ''
            ])

        return response

class ExportFeesView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        # Export fee transaction data to CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="fee_transactions.csv"'

        writer = csv.writer(response)
        writer.writerow(['Transaction ID', 'Student Name', 'Amount Paid', 'Payment Date', 'Status', 'Processed By'])

        # Get filtered transaction data
        transactions = FeeTransaction.objects.select_related(
            'student', 'processed_by'
        ).order_by('-payment_date')

        for transaction in transactions:
            writer.writerow([
                transaction.transaction_id,
                transaction.student.name,
                transaction.amount_paid,
                transaction.payment_date,
                transaction.get_payment_status_display(),
                transaction.processed_by.username if transaction.processed_by else ''
            ])

        return response
