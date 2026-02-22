import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsClient:
    def __init__(self, sheet_id=None):
        self.sheet_id = sheet_id or settings.GOOGLE_SHEETS_ID
        self.client = self._authenticate()
        self.sheet = self.client.open_by_key(self.sheet_id)
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using environment variable"""
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
        
        # Get credentials from environment variable (minified JSON)
        creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        
        if not creds_json:
            # Fallback to environment variable with different name
            creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_JSON')
            
        if creds_json:
            try:
                # Parse the JSON string
                creds_dict = json.loads(creds_json)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                logger.info("✅ Authenticated using GOOGLE_SHEETS_CREDENTIALS environment variable")
                return gspread.authorize(creds)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse GOOGLE_SHEETS_CREDENTIALS JSON: {e}")
                logger.error("Make sure the environment variable contains valid minified JSON")
                raise Exception(f"Invalid JSON in GOOGLE_SHEETS_CREDENTIALS: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to authenticate with credentials from environment: {e}")
                raise
        
        # If no environment variable, try credentials.json file (for local development)
        creds_file = os.path.join(settings.BASE_DIR, 'credentials.json')
        if os.path.exists(creds_file):
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
                logger.info("✅ Authenticated using credentials.json file (local development)")
                return gspread.authorize(creds)
            except Exception as e:
                logger.error(f"❌ Failed to authenticate with credentials.json: {e}")
                raise
        
        # No credentials found
        error_msg = (
            "❌ No Google Sheets credentials found.\n"
            "Please set GOOGLE_SHEETS_CREDENTIALS environment variable with your minified service account JSON.\n"
            "For local development, you can also place credentials.json in the project root."
        )
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def get_deposits_worksheet(self):
        """Get the worksheet containing deposit data (Sheet 2)"""
        try:
            # Try to get worksheet by name first
            return self.sheet.worksheet("Sheet2")
        except gspread.WorksheetNotFound:
            # Fall back to index 1
            return self.sheet.get_worksheet(1)
    
    def get_stocks_worksheet(self):
        """Get the worksheet containing stock data (Sheet 1)"""
        try:
            # Try to get worksheet by name first
            return self.sheet.worksheet("Sheet1")
        except gspread.WorksheetNotFound:
            # Fall back to index 0
            return self.sheet.get_worksheet(0)
    
    def append_deposit(self, deposit):
        """Append deposit data to sheets (Sheet 2)"""
        worksheet = self.get_deposits_worksheet()
        
        # Prepare row data
        row = [
            deposit.created_at.strftime('%Y-%m-%d'),
            deposit.user.email,
            deposit.user.profile.company if hasattr(deposit.user, 'profile') else '',
            str(deposit.amount),
            deposit.payment_method,
            deposit.status,
            deposit.transaction_id,
            deposit.invoice_number or '',
            deposit.stock.symbol if deposit.stock else 'N/A',
            deposit.portfolio.name if deposit.portfolio else 'N/A',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Sync timestamp
        ]
        
        worksheet.append_row(row)
        logger.info(f"Deposit {deposit.transaction_id} appended to sheets")
    
    def get_stock_prices(self):
        """Get latest stock prices from sheets (Sheet 1)"""
        worksheet = self.get_stocks_worksheet()
        logger.info(f"Fetching stock prices from worksheet: {worksheet.title}")
        
        # Get all records
        records = worksheet.get_all_records()
        logger.info(f"Retrieved {len(records)} records from Google Sheets")
        
        # Process records
        price_data = []
        for idx, record in enumerate(records):
            # Debug: print first few records
            if idx < 3:
                logger.info(f"Record {idx}: {record}")
            
            # Only process if symbol exists
            symbol = record.get('Symbol', '').strip()
            if not symbol:
                continue
                
            try:
                # Handle price - could be string or number
                price_val = record.get('Price', 0)
                if isinstance(price_val, str):
                    price_val = price_val.replace('$', '').replace(',', '')
                price = float(price_val or 0)
                
                # Handle previous close
                prev_close_val = record.get('Previous Close', 0)
                if prev_close_val and isinstance(prev_close_val, str):
                    prev_close_val = prev_close_val.replace('$', '').replace(',', '')
                previous_close = float(prev_close_val) if prev_close_val else None
                
                # Handle volume
                volume_val = record.get('Volume', 0)
                if volume_val and isinstance(volume_val, str):
                    volume_val = volume_val.replace(',', '')
                volume = int(float(volume_val)) if volume_val else None
                
                price_data.append({
                    'symbol': symbol,
                    'name': record.get('Name', '').strip() or symbol,
                    'price': price,
                    'previous_close': previous_close,
                    'volume': volume,
                    'last_updated': record.get('Last Updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing record {idx}: {e}")
                continue
        
        logger.info(f"Processed {len(price_data)} valid stock records")
        return price_data
    
    def get_deposits(self):
        """Get deposit data from sheets (Sheet 2)"""
        worksheet = self.get_deposits_worksheet()
        records = worksheet.get_all_records()
        logger.info(f"Retrieved {len(records)} deposit records from Google Sheets")
        return records
    
    def update_stock_price(self, symbol, price, previous_close=None):
        """Update a specific stock price in sheets"""
        worksheet = self.get_stocks_worksheet()
        
        # Find the row with this symbol
        cell = worksheet.find(symbol)
        if cell:
            # Update price (assuming price is in column C)
            worksheet.update_cell(cell.row, 3, price)
            if previous_close:
                worksheet.update_cell(cell.row, 4, previous_close)
            # Update timestamp (assuming column F)
            worksheet.update_cell(cell.row, 6, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return True
        return False
    
    def create_worksheet_if_not_exists(self, title, rows=100, cols=20):
        """Create a worksheet if it doesn't exist"""
        try:
            return self.sheet.worksheet(title)
        except gspread.WorksheetNotFound:
            return self.sheet.add_worksheet(title, rows, cols)