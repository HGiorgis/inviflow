import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from apps.payments.models import Deposit
from apps.core.models import Stock
from apps.core.utils.google_sheets import GoogleSheetsClient
from datetime import datetime

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync data with Google Sheets'
    
    def add_arguments(self, parser):
        parser.add_argument('--direction', type=str, choices=['to_sheets', 'from_sheets', 'both'], default='both')
        parser.add_argument('--sheet-id', type=str, help='Google Sheet ID (optional)')
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Google Sheets sync...'))
        
        try:
            sheet_id = options['sheet_id'] or settings.GOOGLE_SHEETS_ID
            client = GoogleSheetsClient(sheet_id)
            
            if options['direction'] in ['to_sheets', 'both']:
                self.sync_deposits_to_sheets(client)
            
            if options['direction'] in ['from_sheets', 'both']:
                self.sync_prices_from_sheets(client)
                # Optionally sync deposits from sheets to database
                # self.sync_deposits_from_sheets(client)
            
            self.stdout.write(self.style.SUCCESS('Sync completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Sync failed: {str(e)}'))
    
    def sync_deposits_to_sheets(self, client):
        """Sync unsynced deposits to Google Sheets"""
        deposits = Deposit.objects.filter(synced_to_sheets=False)
        
        if not deposits.exists():
            self.stdout.write('No new deposits to sync')
            return
        
        self.stdout.write(f'Syncing {deposits.count()} deposits to sheets...')
        
        for deposit in deposits:
            try:
                client.append_deposit(deposit)
                deposit.synced_to_sheets = True
                deposit.save()
                self.stdout.write(f'  Synced deposit {deposit.transaction_id}')
            except Exception as e:
                logger.error(f'Failed to sync deposit {deposit.id}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'  Failed: {deposit.transaction_id}'))
    
    def sync_prices_from_sheets(self, client):
        """Sync stock prices from Google Sheets (Sheet 1) to database"""
        self.stdout.write('Syncing stock prices from sheets (Sheet 1)...')
        
        try:
            price_data = client.get_stock_prices()
            self.stdout.write(f'Found {len(price_data)} stocks in Google Sheets')
            
            if not price_data:
                self.stdout.write(self.style.WARNING('No stock data found in sheets'))
                return
            
            created = 0
            updated = 0
            
            for data in price_data:
                # Skip empty symbols
                if not data['symbol']:
                    continue
                
                # Try to get existing stock or create new one
                stock, created_flag = Stock.objects.update_or_create(
                    symbol=data['symbol'].upper().strip(),
                    defaults={
                        'name': data.get('name', data['symbol']).strip(),
                        'current_price': data['price'],
                        'previous_close': data.get('previous_close'),
                        'volume': data.get('volume'),
                        'last_updated': timezone.now(),
                        'is_active': True,
                    }
                )
                
                if created_flag:
                    created += 1
                    self.stdout.write(f'  Created new stock: {stock.symbol} - {stock.name}')
                else:
                    updated += 1
                    self.stdout.write(f'  Updated stock: {stock.symbol} - ${stock.current_price}')
            
            self.stdout.write(self.style.SUCCESS(
                f'Created {created} new stocks, updated {updated} existing stocks'
            ))
            
        except Exception as e:
            logger.error(f'Failed to sync prices: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
    
    def sync_deposits_from_sheets(self, client):
        """Optional: Sync deposits from sheets to database"""
        self.stdout.write('Syncing deposits from sheets (Sheet 2)...')
        
        try:
            deposits_data = client.get_deposits()
            self.stdout.write(f'Found {len(deposits_data)} deposits in Google Sheets')
            
            # This would require more complex logic to match users, portfolios, etc.
            # Implement if needed
            
        except Exception as e:
            logger.error(f'Failed to sync deposits: {str(e)}')