from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Deposit, Invoice
from django.contrib import messages
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 0
    readonly_fields = ('pdf_file', 'sent_at', 'created_at')
    can_delete = False

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'status', 'payment_method', 
                   'created_at', 'invoice_status', 'synced_to_sheets')
    list_filter = ('status', 'payment_method', 'synced_to_sheets', 'created_at')
    search_fields = ('transaction_id', 'invoice_number', 'user__email', 'user__username')
    readonly_fields = ('transaction_id', 'invoice_number', 'created_at', 'updated_at', 
                      'completed_at', 'invoice_link')
    raw_id_fields = ('user', 'portfolio', 'stock')
    inlines = [InvoiceInline]
    actions = ['mark_as_completed', 'generate_invoice', 'sync_to_sheets']
    list_editable = ['status']  # Allow inline status editing
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'portfolio', 'stock', 'amount', 'payment_method')
        }),
        ('Status', {
            'fields': ('status', 'synced_to_sheets', 'completed_at', 'invoice_link'),
            'classes': ('wide',)
        }),
        ('Identifiers', {
            'fields': ('transaction_id', 'invoice_number'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def invoice_status(self, obj):
        """Show invoice status with icon"""
        if obj.invoice_pdf:
            return format_html(
                '<span style="color: green;">✓ PDF Ready</span>'
            )
        elif obj.status == 'completed':
            return format_html(
                '<span style="color: orange;">⏳ Generating...</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">○ Not Available</span>'
            )
    invoice_status.short_description = 'Invoice'
    
    def invoice_link(self, obj):
        """Show link to download invoice if available"""
        if obj.invoice_pdf:
            return format_html(
                '<a href="{}" target="_blank">📄 Download Invoice</a>',
                obj.invoice_pdf.url
            )
        return "No invoice generated yet"
    invoice_link.short_description = 'Invoice'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected deposits as completed and generate invoices"""
        updated = 0
        for deposit in queryset:
            if deposit.status != 'completed':
                deposit.status = 'completed'
                deposit.save()
                updated += 1
                
                # Trigger invoice generation
                from apps.core.utils.pdf_generator import generate_invoice_pdf
                from django.core.files.base import ContentFile
                
                try:
                    pdf_content = generate_invoice_pdf(deposit)
                    filename = f"invoice_{deposit.invoice_number}.pdf"
                    deposit.invoice_pdf.save(filename, ContentFile(pdf_content), save=True)
                except Exception as e:
                    logger.error(f"Failed to generate invoice for deposit {deposit.id}: {e}")
        
        self.message_user(
            request, 
            f'{updated} deposits marked as completed and invoices generated.',
            level=messages.SUCCESS
        )
    mark_as_completed.short_description = "✓ Mark as Completed & Generate Invoice"
    
    def generate_invoice(self, request, queryset):
        """Manually generate invoices for selected deposits"""
        generated = 0
        failed = 0
        
        for deposit in queryset:
            if deposit.status == 'completed' and not deposit.invoice_pdf:
                try:
                    from apps.core.utils.pdf_generator import generate_invoice_pdf
                    from django.core.files.base import ContentFile
                    
                    pdf_content = generate_invoice_pdf(deposit)
                    filename = f"invoice_{deposit.invoice_number}.pdf"
                    deposit.invoice_pdf.save(filename, ContentFile(pdf_content), save=True)
                    generated += 1
                except Exception as e:
                    logger.error(f"Failed to generate invoice: {e}")
                    failed += 1
            elif deposit.invoice_pdf:
                failed += 1  # Already has invoice
        
        if generated:
            self.message_user(
                request,
                f'Generated {generated} invoices. {failed} skipped.',
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                f'No invoices generated. {failed} deposits already have invoices or are not completed.',
                level=messages.WARNING
            )
    generate_invoice.short_description = "📄 Generate Invoice for Selected"
    
    def sync_to_sheets(self, request, queryset):
        """Sync selected deposits to Google Sheets"""
        from apps.core.utils.google_sheets import GoogleSheetsClient
        client = GoogleSheetsClient()
        success = 0
        failed = 0
        
        for deposit in queryset:
            try:
                client.append_deposit(deposit)
                deposit.synced_to_sheets = True
                deposit.save()
                success += 1
            except Exception as e:
                logger.error(f"Failed to sync deposit {deposit.id}: {e}")
                failed += 1
        
        self.message_user(
            request,
            f'Synced {success} deposits to sheets, {failed} failed.',
            level=messages.SUCCESS if success else messages.ERROR
        )
    sync_to_sheets.short_description = "🔄 Sync Selected to Google Sheets"

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('deposit', 'created_at', 'sent_to_email', 'sent_at', 'download_link')
    list_filter = ('sent_to_email', 'created_at')
    search_fields = ('deposit__transaction_id', 'deposit__user__email')
    readonly_fields = ('pdf_file', 'created_at', 'updated_at')
    
    def download_link(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank">📥 Download</a>',
                obj.pdf_file.url
            )
        return "-"
    download_link.short_description = 'Download'