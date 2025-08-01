from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date, datetime

class Shift(models.Model):
    SHIFT_CHOICES = [
        ('MORNING', 'Morning'),
        ('NOON', 'Noon'),
        ('EVENING', 'Evening'),
    ]

    name = models.CharField(max_length=20, choices=SHIFT_CHOICES, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_name_display()

class Student(models.Model):
    FEE_STATUS_CHOICES = [
        ('DUE', 'Due'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    enrolled_shifts = models.ManyToManyField(Shift, related_name='students')
    single_shift_fee = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    discount_applied = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fee_status = models.CharField(max_length=10, choices=FEE_STATUS_CHOICES, default='DUE')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def calculate_total_fee(self):
        """Calculate total fee based on enrolled shifts and discounts"""
        num_shifts = self.enrolled_shifts.count()
        if num_shifts == 0:
            return 0

        # Get fee configuration
        config = FeeConfiguration.get_instance()
        base_fee = config.base_single_shift_fee

        total_fee = base_fee * num_shifts

        # Apply discounts
        if num_shifts == 2:
            discount = (config.discount_two_shifts / 100) * total_fee
        elif num_shifts >= 3:
            discount = (config.discount_three_plus_shifts / 100) * total_fee
        else:
            discount = 0

        self.single_shift_fee = base_fee
        self.discount_applied = discount
        final_fee = total_fee - discount

        return final_fee

    def get_shifts_display(self):
        """Return comma-separated list of enrolled shifts"""
        return ", ".join([shift.get_name_display() for shift in self.enrolled_shifts.all()])

    def get_total_paid(self):
        """Calculate total amount paid by student"""
        return self.fee_transactions.filter(
            payment_status='COMPLETED'
        ).aggregate(
            total=models.Sum('amount_paid')
        )['total'] or Decimal('0.00')

    def get_remaining_due(self):
        """Calculate remaining due amount"""
        total_fee = self.calculate_total_fee()
        total_paid = self.get_total_paid()
        return max(Decimal('0.00'), Decimal(str(total_fee)) - total_paid)

    def update_fee_status(self):
        """Update fee status based on payments"""
        remaining_due = self.get_remaining_due()
        if remaining_due <= 0:
            self.fee_status = 'PAID'
        elif remaining_due > 0:
            # Check if payment is overdue (more than 30 days)
            last_payment = self.fee_transactions.filter(
                payment_status='COMPLETED'
            ).order_by('-payment_date').first()

            if last_payment:
                days_since_payment = (date.today() - last_payment.payment_date).days
                if days_since_payment > 30:
                    self.fee_status = 'OVERDUE'
                else:
                    self.fee_status = 'DUE'
            else:
                days_since_enrollment = (date.today() - self.date_enrolled.date()).days
                if days_since_enrollment > 30:
                    self.fee_status = 'OVERDUE'
                else:
                    self.fee_status = 'DUE'

        self.total_due_amount = remaining_due
        self.save()

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['student', 'shift', 'date']
        ordering = ['-date', 'shift', 'student']

    def __str__(self):
        return f"{self.student.name} - {self.shift} - {self.date} - {self.status}"

class FeeTransaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_transactions')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='COMPLETED')
    remaining_due_after_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.student.name} - ₹{self.amount_paid} - {self.payment_date}"

    def save(self, *args, **kwargs):
        # Generate transaction ID if not provided
        if not self.transaction_id:
            self.transaction_id = f"TXN{self.student.id}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        super().save(*args, **kwargs)

        # Update student's fee status after saving transaction
        if self.payment_status == 'COMPLETED':
            self.student.update_fee_status()

class FeeConfiguration(models.Model):
    base_single_shift_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1000.00,
        validators=[MinValueValidator(0)]
    )
    discount_two_shifts = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage for 2 enrolled shifts"
    )
    discount_three_plus_shifts = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage for 3 or more enrolled shifts"
    )
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fee Configuration"
        verbose_name_plural = "Fee Configuration"

    def __str__(self):
        return f"Fee Config - Base: ₹{self.base_single_shift_fee}"

    @classmethod
    def get_instance(cls):
        """Get or create the single fee configuration instance"""
        config, created = cls.objects.get_or_create(pk=1)
        return config

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ADMIN')
    phone_number = models.CharField(max_length=15, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_users')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def is_super_admin(self):
        return self.role == 'SUPER_ADMIN'

    @property
    def is_admin(self):
        return self.role in ['ADMIN', 'SUPER_ADMIN']