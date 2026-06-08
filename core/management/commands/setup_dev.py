"""
Management command to seed the database with a dev organisation,
admin user, and sample roles for quick local development.

Usage: python manage.py setup_dev
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Organisation, BusinessUnit, Department, User


class Command(BaseCommand):
    help = 'Seed development data: organisation, users, departments'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up MAGHAZ Assist dev environment...')

        # Organisation
        org, _ = Organisation.objects.get_or_create(
            slug='maghaz',
            defaults={
                'name': 'MAGHAZ',
                'email': 'admin@maghaz.com',
                'phone': '+233200000000',
                'address': 'Accra, Ghana',
            }
        )
        self.stdout.write(f'  ✓ Organisation: {org.name}')

        # Business Units
        units = [
            ('MAGHAZ Hotel', BusinessUnit.UnitType.HOSPITALITY),
            ('MAGHAZ Properties', BusinessUnit.UnitType.REAL_ESTATE),
            ('MAGHAZ Construction', BusinessUnit.UnitType.CONSTRUCTION),
            ('MAGHAZ Transport', BusinessUnit.UnitType.TRANSPORT),
            ('Administration', BusinessUnit.UnitType.ADMINISTRATION),
        ]
        for name, unit_type in units:
            BusinessUnit.objects.get_or_create(
                organisation=org, name=name,
                defaults={'unit_type': unit_type}
            )
        self.stdout.write(f'  ✓ Business units: {len(units)} created')

        # Departments
        departments = [
            'Front Office', 'Housekeeping', 'Food & Beverage',
            'Property Management', 'Construction Projects',
            'Human Resources', 'Finance & Accounts',
            'Maintenance', 'Transport Operations', 'IT & Systems',
        ]
        for dept_name in departments:
            Department.objects.get_or_create(organisation=org, name=dept_name)
        self.stdout.write(f'  ✓ Departments: {len(departments)} created')

        # Seed users for each role
        seed_users = [
            ('admin@maghazassist.com',       'Admin',     'User',       User.Role.SYSTEM_ADMIN),
            ('executive@maghazassist.com',   'Executive', 'Director',   User.Role.EXECUTIVE),
            ('hotel@maghazassist.com',       'Hotel',     'Manager',    User.Role.HOTEL_MANAGER),
            ('frontdesk@maghazassist.com',   'Front',     'Desk',       User.Role.FRONT_DESK),
            ('property@maghazassist.com',    'Property',  'Manager',    User.Role.PROPERTY_MANAGER),
            ('construction@maghazassist.com','Project',   'Manager',    User.Role.CONSTRUCTION_PM),
            ('site@maghazassist.com',        'Site',      'Supervisor', User.Role.SITE_SUPERVISOR),
            ('hr@maghazassist.com',          'HR',        'Manager',    User.Role.HR_MANAGER),
            ('finance@maghazassist.com',     'Finance',   'Officer',    User.Role.FINANCE_OFFICER),
            ('maintenance@maghazassist.com', 'Maintenance','Tech',      User.Role.MAINTENANCE_TEAM),
            ('dispatch@maghazassist.com',    'Transport', 'Dispatcher', User.Role.TRANSPORT_DISPATCHER),
            ('driver@maghazassist.com',      'Internal',  'Driver',     User.Role.INTERNAL_DRIVER),
            ('3pdriver@maghazassist.com',    'ThirdParty','Driver',     User.Role.THIRD_PARTY_DRIVER),
            ('tenant@maghazassist.com',      'Sample',    'Tenant',     User.Role.TENANT),
            ('guest@maghazassist.com',       'Sample',    'Guest',      User.Role.GUEST),
        ]

        created = 0
        for email, first, last, role in seed_users:
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email,
                    password='Test1234!',
                    first_name=first,
                    last_name=last,
                    role=role,
                    organisation=org,
                )
                created += 1

        self.stdout.write(f'  ✓ Users: {created} created (password: Test1234!)')
        self.stdout.write(self.style.SUCCESS('\nDev setup complete. Start your server and log in!'))
