from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import FileResponse
from django.core.files.base import ContentFile
from .models import Deposit, Invoice
from apps.portfolio.models import Portfolio
from apps.core.models import Stock
from apps.core.utils.pdf_generator import generate_invoice_pdf
from apps.core.utils.google_sheets import GoogleSheetsClient
import io

class DepositListView(LoginRequiredMixin, ListView):
    model = Deposit
    template_name = 'payments/deposit_list.html'
    context_object_name = 'deposits'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Deposit.objects.all().select_related('user', 'portfolio', 'stock')
        return Deposit.objects.filter(user=self.request.user).select_related('portfolio', 'stock')

class DepositDetailView(LoginRequiredMixin, DetailView):
    model = Deposit
    template_name = 'payments/deposit_detail.html'
    context_object_name = 'deposit'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Deposit.objects.all()
        return Deposit.objects.filter(user=self.request.user)

class DepositCreateView(LoginRequiredMixin, CreateView):
    model = Deposit
    template_name = 'payments/deposit_form.html'
    fields = ['portfolio', 'stock', 'amount', 'payment_method']
    success_url = reverse_lazy('payments:deposit_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['portfolio'].queryset = Portfolio.objects.filter(user=self.request.user)
        form.fields['stock'].queryset = Stock.objects.filter(is_active=True)
        form.fields['stock'].required = False
        return form
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'pending'
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            f'Deposit of ${form.instance.amount} created successfully! Status: Pending'
        )
        
        return response

class DownloadInvoiceView(LoginRequiredMixin, View):
    def get(self, request, pk):
        deposit = get_object_or_404(Deposit, pk=pk)
        
        # Check permission
        if not request.user.is_superuser and deposit.user != request.user:
            messages.error(request, 'You do not have permission to view this invoice')
            return redirect('payments:deposit_list')
        
        # If no invoice yet but deposit is completed, generate it
        if not deposit.invoice_pdf and deposit.status == 'completed':
            from apps.core.utils.pdf_generator import generate_invoice_pdf
            from django.core.files.base import ContentFile
            
            try:
                pdf_content = generate_invoice_pdf(deposit)
                filename = f"invoice_{deposit.invoice_number}.pdf"
                deposit.invoice_pdf.save(filename, ContentFile(pdf_content), save=True)
                messages.success(request, 'Invoice generated successfully!')
            except Exception as e:
                logger.error(f"Failed to generate invoice: {e}")
                messages.error(request, 'Could not generate invoice. Please try again.')
                return redirect('payments:deposit_detail', pk=pk)
        
        # Serve the file
        if deposit.invoice_pdf:
            response = FileResponse(
                deposit.invoice_pdf.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="invoice_{deposit.invoice_number}.pdf"'
            return response
        
        messages.error(request, 'Invoice not available')
        return redirect('payments:deposit_detail', pk=pk)
class SyncToSheetsView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_superuser:
            messages.error(request, 'Only admins can manually sync to sheets')
            return redirect('payments:deposit_detail', pk=pk)
        
        deposit = get_object_or_404(Deposit, pk=pk)
        
        try:
            client = GoogleSheetsClient()
            client.append_deposit(deposit)
            deposit.synced_to_sheets = True
            deposit.save()
            messages.success(request, f'Deposit {deposit.transaction_id} synced to Google Sheets')
        except Exception as e:
            messages.error(request, f'Failed to sync: {str(e)}')
        
        return redirect('payments:deposit_detail', pk=pk)

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'payments/invoice_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Invoice.objects.all().select_related('deposit')
        return Invoice.objects.filter(deposit__user=self.request.user).select_related('deposit')