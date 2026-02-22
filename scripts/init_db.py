#!/usr/bin/env python
"""
Initial database setup script for InviFlow
Run this after migrations to populate initial data
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inviflow.settings')
django.setup()

from django.contrib.auth.models import User
from apps.core.models import Stock, Profile
from apps.portfolio.models import Portfolio
import random
from decimal import Decimal

def create_test_users():
    """Create test users"""
    print("Creating test users...")
    
    users_data = [
        {'username': 'john', 'email': 'john@example.com', 'password': 'password123', 'first_name': 'John', 'last_name': 'Doe'},
        {'username': 'jane', 'email': 'jane@example.com', 'password': 'password123', 'first_name': 'Jane', 'last_name': 'Smith'},
        {'username': 'bob', 'email': 'bob@example.com', 'password': 'password123', 'first_name': 'Bob', 'last_name': 'Johnson'},
    ]
    
    for data in users_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
            Profile.objects.create(user=user)
            print(f"  Created user: {user.username}")
        else:
            print(f"  User already exists: {user.username}")

def create_stocks():
    """Create sample stocks"""
    print("\nCreating sample stocks...")
    
    stocks_data = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 175.50, 'volume': 55000000},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'price': 140.25, 'volume': 22000000},
        {'symbol': 'MSFT', 'name': 'Microsoft Corp.', 'price': 380.75, 'volume': 28000000},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'price': 145.80, 'volume': 35000000},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'price': 240.50, 'volume': 120000000},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'price': 330.20, 'volume': 18000000},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corp.', 'price': 480.90, 'volume': 40000000},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.', 'price': 155.30, 'volume': 15000000},
        {'symbol': 'V', 'name': 'Visa Inc.', 'price': 250.60, 'volume': 8000000},
        {'symbol': 'WMT', 'name': 'Walmart Inc.', 'price': 165.40, 'volume': 5000000},
    ]
    
    for data in stocks_data:
        stock, created = Stock.objects.get_or_create(
            symbol=data['symbol'],
            defaults={
                'name': data['name'],
                'current_price': data['price'],
                'previous_close': data['price'] * 0.98,
                'volume': data['volume'],
                'is_active': True,
            }
        )
        if created:
            print(f"  Created stock: {stock.symbol}")
        else:
            print(f"  Stock already exists: {stock.symbol}")

def create_portfolios():
    """Create portfolios for users"""
    print("\nCreating portfolios...")
    
    users = User.objects.filter(is_superuser=False)
    stocks = list(Stock.objects.all())
    
    for user in users:
        # Create main portfolio if not exists
        portfolio, created = Portfolio.objects.get_or_create(
            user=user,
            name='Main Portfolio',
            defaults={'description': 'My main investment portfolio'}
        )
        
        if created:
            print(f"  Created portfolio for {user.username}")
            
            # Add some random holdings
            from apps.portfolio.models import Holding
            
            for _ in range(random.randint(2, 5)):
                stock = random.choice(stocks)
                quantity = Decimal(random.randint(10, 100))
                price = stock.current_price * Decimal(0.95 + random.random() * 0.1)
                
                Holding.objects.create(
                    portfolio=portfolio,
                    stock=stock,
                    quantity=quantity,
                    average_buy_price=price
                )
            
            portfolio.update_total_value()
            print(f"    Added {portfolio.holdings.count()} holdings")

def main():
    print("=" * 50)
    print("InviFlow - Database Initialization")
    print("=" * 50)
    
    create_test_users()
    create_stocks()
    create_portfolios()
    
    print("\n" + "=" * 50)
    print("Initialization complete!")
    print("=" * 50)
    print("\nTest users created:")
    print("  john / password123")
    print("  jane / password123")
    print("  bob / password123")
    print("\nAdmin user (if created separately):")
    print("  Use: python manage.py createsuperuser")

if __name__ == '__main__':
    main()