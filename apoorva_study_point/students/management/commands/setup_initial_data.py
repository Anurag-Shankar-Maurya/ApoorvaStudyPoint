from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from students.models import Shift, FeeConfiguration, UserProfile
from datetime import time

class Command(BaseCommand):
    help = 'Setup initial data for Apoorva Study Point'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up initial data...'))

        # Create shifts
        shifts_data = [
            ('MORNING', time(9, 0), time(12, 0)),
            ('NOON', time(13, 0), time(16, 0)),
            ('EVENING', time(17, 0), time(20, 0)),
        ]

        for name, start_time, end_time in shifts_data:
            shift, created = Shift.objects.get_or_create(
                name=name,
                defaults={
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created shift: {shift.get_name_display()}')

        # Create fee configuration
        config = FeeConfiguration.get_instance()
        self.stdout.write('Fee configuration initialized')

        # Create super admin user
        if not User.objects.filter(username='superadmin').exists():
            super_admin = User.objects.create_user(
                username='superadmin',
                password='admin123',
                email='admin@apoorva.com',
                is_staff=True,
                is_superuser=True
            )
            UserProfile.objects.create(
                user=super_admin,
                role='SUPER_ADMIN'
            )
            self.stdout.write('Created super admin user: superadmin/admin123')

        # Create regular admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                password='admin123',
                email='staff@apoorva.com'
            )
            UserProfile.objects.create(
                user=admin_user,
                role='ADMIN'
            )
            self.stdout.write('Created admin user: admin/admin123')

        # Create demo users from original website
        demo_users = [
            ('Super', 'Super@12345', 'SUPER_ADMIN'),
        ]

        for username, password, role in demo_users:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=f'{username.lower()}@apoorva.com'
                )
                UserProfile.objects.create(
                    user=user,
                    role=role
                )
                self.stdout.write(f'Created demo user: {username}/{password}')

        self.stdout.write(self.style.SUCCESS('Initial data setup completed!'))
        self.stdout.write(self.style.WARNING('Login credentials:'))
        self.stdout.write('Super Admin: superadmin/admin123 or Super/Super@12345')
        self.stdout.write('Admin: admin/admin123')
