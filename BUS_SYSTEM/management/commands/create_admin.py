from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from BUS_SYSTEM.models import Profile

class Command(BaseCommand):
    help = 'Create an admin user with profile'
    
    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)
    
    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User "{username}" already exists!'))
            return
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Create profile with admin role
            profile = Profile.objects.create(
                user=user,
                role='admin'
            )
            
            self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created successfully!'))
            self.stdout.write(f'\nLogin credentials:')
            self.stdout.write(f'  Username: {username}')
            self.stdout.write(f'  Password: {password}')
            self.stdout.write(f'  Role: Admin')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))