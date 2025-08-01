from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, ButtonHolder, Submit, Row, Column
from .models import Student, Attendance, FeeTransaction, FeeConfiguration, UserProfile, Shift

class StudentForm(forms.ModelForm):
    enrolled_shifts = forms.ModelMultipleChoiceField(
        queryset=Shift.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Student
        fields = ['name', 'contact', 'address', 'enrolled_shifts', 'fee_status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter student name'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'fee_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('contact', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'address',
            Fieldset(
                'Enrolled Shifts',
                'enrolled_shifts',
                css_class='mb-3'
            ),
            'fee_status',
            ButtonHolder(
                Submit('submit', 'Save Student', css_class='btn btn-primary')
            )
        )

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'shift', 'date', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('student', css_class='form-group col-md-4 mb-0'),
                Column('shift', css_class='form-group col-md-4 mb-0'),
                Column('date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('status', css_class='form-group col-md-6 mb-0'),
                Column('notes', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            ButtonHolder(
                Submit('submit', 'Mark Attendance', css_class='btn btn-primary')
            )
        )

class BulkAttendanceForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.students = kwargs.pop('students', [])
        super().__init__(*args, **kwargs)

        # Dynamically add attendance fields for each student
        for student in self.students:
            field_name = f'student_{student.id}'
            self.fields[field_name] = forms.ChoiceField(
                choices=Attendance.STATUS_CHOICES,
                initial='PRESENT',
                widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
                label=student.name
            )

class FeeTransactionForm(forms.ModelForm):
    class Meta:
        model = FeeTransaction
        fields = ['student', 'amount_paid', 'payment_date', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'student',
            Row(
                Column('amount_paid', css_class='form-group col-md-6 mb-0'),
                Column('payment_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'notes',
            ButtonHolder(
                Submit('submit', 'Record Payment', css_class='btn btn-success')
            )
        )

class FeeConfigurationForm(forms.ModelForm):
    class Meta:
        model = FeeConfiguration
        fields = ['base_single_shift_fee', 'discount_two_shifts', 'discount_three_plus_shifts']
        widgets = {
            'base_single_shift_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_two_shifts': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'max': '100', 'min': '0'}),
            'discount_three_plus_shifts': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'max': '100', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'base_single_shift_fee',
            Row(
                Column('discount_two_shifts', css_class='form-group col-md-6 mb-0'),
                Column('discount_three_plus_shifts', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            ButtonHolder(
                Submit('submit', 'Update Configuration', css_class='btn btn-primary')
            )
        )

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['role', 'phone_number']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('role', css_class='form-group col-md-6 mb-0'),
                Column('phone_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            ButtonHolder(
                Submit('submit', 'Create User', css_class='btn btn-primary')
            )
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone_number=self.cleaned_data['phone_number']
            )
        return user

class StudentSearchForm(forms.Form):
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or contact...'
        })
    )
    shift_filter = forms.ModelChoiceField(
        queryset=Shift.objects.filter(is_active=True),
        required=False,
        empty_label="All Shifts",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fee_status_filter = forms.ChoiceField(
        choices=[('', 'All Status')] + Student.FEE_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class AttendanceFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    shift_filter = forms.ModelChoiceField(
        queryset=Shift.objects.filter(is_active=True),
        required=False,
        empty_label="All Shifts",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student_filter = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class FeeTransactionFilterForm(forms.Form):
    status_filter = forms.ChoiceField(
        choices=[('', 'All Status')] + FeeTransaction.PAYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    month_filter = forms.CharField(
        max_length=7,
        required=False,
        widget=forms.TextInput(attrs={'type': 'month', 'class': 'form-control'})
    )
    shift_filter = forms.ModelChoiceField(
        queryset=Shift.objects.filter(is_active=True),
        required=False,
        empty_label="All Shifts",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
