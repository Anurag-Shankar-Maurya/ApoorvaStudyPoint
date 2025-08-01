# Apoorva Study Point Management System

A comprehensive Django-based student management system for coaching centers and study points. This system replicates and enhances the functionality of the original Apoorva Study Point web application with a full Django backend implementation.

## Features

### 🎯 Core Functionality
- **Student Management**: Add, edit, delete, and search students with shift enrollment
- **Attendance Management**: Mark daily attendance, bulk attendance, and attendance tracking
- **Fee Management**: Record fee payments, track due amounts, and payment history
- **Analytics & Reports**: Comprehensive reports and data visualization
- **User Management**: Multi-level admin access (Super Admin, Admin)
- **Fee Configuration**: Flexible fee structure with discount management

### 📊 Dashboard Features
- Real-time statistics (Total Students, Revenue, Pending Fees)
- Interactive charts for attendance and fee collection
- Time-based data filtering (This Month, Last 30 Days, This Year)
- Responsive design for all devices

### 👥 User Management
- **Super Admin**: Full system access, user management, configuration
- **Admin**: Student and attendance management, fee recording
- Role-based permissions and access control

### 💰 Fee Management
- Automatic fee calculation based on enrolled shifts
- Discount system for multiple shift enrollments
- Fee status tracking (Due, Paid, Overdue)
- Payment history and transaction records

### 📈 Analytics & Reporting
- Student attendance percentage tracking
- Fee collection analysis
- Export functionality (CSV format)
- Detailed student performance reports

## Technology Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite (default) / PostgreSQL (production ready)
- **Frontend**: Bootstrap 5, Chart.js
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Export**: CSV, ReportLab for PDF generation
- **Authentication**: Django built-in authentication with custom profiles

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Installation

1. **Clone or download the project files**
   ```bash
   # If you have the project as a zip file, extract it
   # Or copy all the generated files to your project directory
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Set up initial data**
   ```bash
   python manage.py setup_initial_data
   ```

7. **Create superuser** (optional - initial users are already created)
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   Open your browser and go to: `http://127.0.0.1:8000`

## Default Login Credentials

After running the setup command, you can use these credentials:

### Super Admin Access
- Username: `superadmin` Password: `admin123`
- Username: `Super` Password: `Super@12345`

### Regular Admin Access
- Username: `admin` Password: `admin123`

## System Architecture

### Models
- **Student**: Core student information, fee status, shift enrollments
- **Shift**: Time-based study sessions (Morning, Noon, Evening)
- **Attendance**: Daily attendance records with status tracking
- **FeeTransaction**: Payment records and transaction history
- **FeeConfiguration**: System-wide fee and discount settings
- **UserProfile**: Extended user information with role management

### Key Features Implementation

#### Fee Calculation Logic
- Base fee per shift with automatic discount application
- 2 shifts: Configurable discount percentage
- 3+ shifts: Higher discount percentage
- Real-time due amount calculation

#### Attendance System
- Individual and bulk attendance marking
- Status options: Present, Absent, Late
- Date and shift-based filtering
- Attendance percentage calculations

#### Reporting System
- CSV export for attendance and fee data
- Dashboard analytics with charts
- Student performance summaries
- Financial reporting

## File Structure

```
apoorva_study_point/
├── apoorva_study_point/
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── students/
│   ├── management/
│   │   └── commands/
│   │       └── setup_initial_data.py  # Initial setup command
│   ├── migrations/         # Database migrations
│   ├── __init__.py
│   ├── admin.py           # Django admin configuration
│   ├── forms.py           # Form definitions
│   ├── models.py          # Database models
│   ├── urls.py            # App URL patterns
│   └── views.py           # Business logic and views
├── templates/
│   ├── base.html          # Base template
│   ├── login.html         # Login page
│   ├── dashboard.html     # Main dashboard
│   ├── students/          # Student management templates
│   ├── attendance/        # Attendance templates
│   ├── fees/              # Fee management templates
│   ├── analytics/         # Reports and analytics
│   ├── admin_management/  # User management
│   └── config/            # System configuration
├── static/
│   └── css/
│       └── style.css      # Custom styles
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Usage Guide

### Adding Students
1. Navigate to Students → Add New Student
2. Fill in student details and select shifts
3. System automatically calculates fees based on enrolled shifts

### Managing Attendance
1. Go to Attendance Management
2. Use "Mark Attendance" for individual entries
3. Use "Bulk Attendance" for entire shift groups
4. Filter and view attendance history

### Recording Fee Payments
1. Access Fee Management
2. Click "Record New Payment"
3. Select student and enter payment details
4. System updates due amounts automatically

### Viewing Reports
1. Navigate to Analytics & Reports
2. View attendance and fee summaries
3. Export data using the export buttons
4. Access detailed charts and statistics

### System Configuration
1. Super Admin can access Admin → Fee Configuration
2. Update base fees and discount percentages
3. Manage user accounts and permissions

## Customization

### Adding New Features
The system is built with Django best practices and can be easily extended:

- Add new models in `students/models.py`
- Create corresponding forms in `students/forms.py`
- Implement views in `students/views.py`
- Add URL patterns in `students/urls.py`
- Create templates following the existing structure

### Styling Customization
- Modify `static/css/style.css` for custom styles
- Templates use Bootstrap 5 for responsive design
- Chart.js integration for data visualization

## Deployment

### Production Setup
1. Set `DEBUG=False` in settings
2. Configure proper database (PostgreSQL recommended)
3. Set up static file serving
4. Configure secure secret key
5. Set allowed hosts

### Environment Variables
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Troubleshooting

### Common Issues

1. **Migration Errors**
   ```bash
   python manage.py makemigrations students
   python manage.py migrate
   ```

2. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic
   ```

3. **Permission Denied**
   - Ensure user has proper role assignment
   - Check UserProfile creation

4. **Chart Not Loading**
   - Ensure internet connection for CDN resources
   - Check browser console for JavaScript errors

## Contributing

This system is designed to be maintainable and extensible. When contributing:

1. Follow Django best practices
2. Maintain consistent coding style
3. Update documentation for new features
4. Test thoroughly before deployment

## License

This project is developed for educational and business use. Please ensure compliance with your organization's requirements.

## Support

For technical support or customization requests, please refer to the Django documentation or contact the development team.

---

**Note**: This is a complete implementation of the Apoorva Study Point management system with all features from the original web application plus additional enhancements for better functionality and user experience.
