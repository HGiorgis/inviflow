from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('deposits/', views.DepositListView.as_view(), name='deposit_list'),
    path('deposits/create/', views.DepositCreateView.as_view(), name='deposit_create'),
    path('deposits/<int:pk>/', views.DepositDetailView.as_view(), name='deposit_detail'),
    path('deposits/<int:pk>/invoice/', views.DownloadInvoiceView.as_view(), name='download_invoice'),
    path('deposits/<int:pk>/sync-to-sheets/', views.SyncToSheetsView.as_view(), name='sync_to_sheets'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
]