from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from .models import Portfolio, Holding
from apps.core.models import Stock
from decimal import Decimal
import json

class PortfolioListView(LoginRequiredMixin, ListView):
    model = Portfolio
    template_name = 'portfolio/list.html'
    context_object_name = 'portfolios'
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

class PortfolioDetailView(LoginRequiredMixin, DetailView):
    model = Portfolio
    template_name = 'portfolio/detail.html'
    context_object_name = 'portfolio'
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        portfolio = self.get_object()
        
        # Update total value
        portfolio.update_total_value()
        
        # Get holdings with calculated values
        holdings = portfolio.holdings.select_related('stock').all()
        for holding in holdings:
            holding.current_value = holding.current_value
            holding.profit_loss = holding.profit_loss
            holding.profit_loss_percent = holding.profit_loss_percent
        
        context['holdings'] = holdings
        
        # Calculate portfolio statistics
        total_invested = sum(h.quantity * h.average_buy_price for h in holdings)
        total_current = sum(h.current_value for h in holdings)
        
        context['total_invested'] = total_invested
        context['total_current'] = total_current
        context['total_profit_loss'] = total_current - total_invested
        if total_invested:
            context['total_profit_loss_percent'] = ((total_current - total_invested) / total_invested) * 100
        else:
            context['total_profit_loss_percent'] = 0
        
        # Chart data for allocation
        labels = [h.stock.symbol for h in holdings[:10]]
        data = [float(h.current_value) for h in holdings[:10]]
        
        context['chart_labels'] = json.dumps(labels)
        context['chart_data'] = json.dumps(data)
        
        return context

class PortfolioCreateView(LoginRequiredMixin, CreateView):
    model = Portfolio
    template_name = 'portfolio/form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('portfolio:list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Portfolio created successfully!')
        return super().form_valid(form)

class PortfolioUpdateView(LoginRequiredMixin, UpdateView):
    model = Portfolio
    template_name = 'portfolio/form.html'
    fields = ['name', 'description']
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('portfolio:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Portfolio updated successfully!')
        return super().form_valid(form)

class AddHoldingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
        
        stock_id = request.POST.get('stock_id')
        quantity = request.POST.get('quantity')
        price = request.POST.get('price')
        
        try:
            stock = Stock.objects.get(id=stock_id, is_active=True)
            
            # Create or update holding
            holding, created = Holding.objects.update_or_create(
                portfolio=portfolio,
                stock=stock,
                defaults={
                    'quantity': Decimal(quantity),
                    'average_buy_price': Decimal(price)
                }
            )
            
            portfolio.update_total_value()
            
            if created:
                messages.success(request, f'Added {stock.symbol} to portfolio')
            else:
                messages.success(request, f'Updated {stock.symbol} holding')
                
        except Stock.DoesNotExist:
            messages.error(request, 'Stock not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('portfolio:detail', pk=portfolio.pk)

class UpdateHoldingView(LoginRequiredMixin, UpdateView):
    model = Holding
    template_name = 'portfolio/holding_form.html'
    fields = ['quantity', 'average_buy_price']
    
    def get_queryset(self):
        return Holding.objects.filter(portfolio__user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('portfolio:detail', kwargs={'pk': self.object.portfolio.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Holding updated successfully!')
        response = super().form_valid(form)
        self.object.portfolio.update_total_value()
        return response

class DeleteHoldingView(LoginRequiredMixin, DeleteView):
    model = Holding
    template_name = 'portfolio/holding_confirm_delete.html'
    
    def get_queryset(self):
        return Holding.objects.filter(portfolio__user=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, 'Holding removed from portfolio')
        return reverse_lazy('portfolio:detail', kwargs={'pk': self.object.portfolio.pk})

class StockChartView(LoginRequiredMixin, View):
    def get(self, request, stock_id):
        stock = get_object_or_404(Stock, id=stock_id)
        
        # Mock chart data for the stock
        import random
        from datetime import datetime, timedelta
        
        dates = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30, 0, -1)]
        prices = [float(stock.current_price) * (1 + (random.random() - 0.5) * 0.1) for _ in range(30)]
        
        return JsonResponse({
            'labels': dates,
            'prices': prices,
            'symbol': stock.symbol
        })