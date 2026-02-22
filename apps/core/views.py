from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView, View
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q
from .models import Stock, Profile
from apps.portfolio.models import Portfolio, Holding, ChartView
from apps.payments.models import Deposit
from datetime import datetime, timedelta
import json
from decimal import Decimal
from .forms import CustomUserCreationForm 

    
class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['total_stocks'] = Stock.objects.count()
        context['total_deposits'] = Deposit.objects.filter(status='completed').count()
        context['top_stocks'] = Stock.objects.filter(is_active=True).order_by('-current_price')[:5]
        return context

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user portfolios
        portfolios = Portfolio.objects.filter(user=user)
        context['portfolios'] = portfolios
        
        # Get recent deposits
        context['recent_deposits'] = Deposit.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Calculate total portfolio value
        total_value = 0
        for portfolio in portfolios:
            portfolio.update_total_value()
            total_value += portfolio.total_value
        context['total_portfolio_value'] = total_value
        
        # Get recently viewed stocks
        recent_views = ChartView.objects.filter(user=user).select_related('stock')[:5]
        context['recent_stocks'] = [view.stock for view in recent_views]
        
        # Chart data for portfolio performance (mock data for demo)
        labels = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30, 0, -1)]
        data = [float(total_value) * (1 + (x/1000)) for x in range(30)]
        
        context['chart_labels'] = json.dumps(labels)
        context['chart_data'] = json.dumps(data)
        
        return context

class ProfileView(LoginRequiredMixin, View):
    template_name = 'core/profile.html'
    
    def get(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Statistics
        total_deposits = Deposit.objects.filter(user=request.user, status='completed').count()
        total_invested = Deposit.objects.filter(
            user=request.user, status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        recent_deposits = Deposit.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        context = {
            'profile': profile,
            'total_deposits': total_deposits,
            'total_invested': total_invested,
            'recent_deposits': recent_deposits,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Update user info
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        
        # Update profile
        profile.phone = request.POST.get('phone', '')
        profile.company = request.POST.get('company', '')
        profile.address = request.POST.get('address', '')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('core:profile')

class StockListView(ListView):
    model = Stock
    template_name = 'core/stock_list.html'
    context_object_name = 'stocks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Stock.objects.filter(is_active=True)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(symbol__icontains=search) | Q(name__icontains=search)
            )
        
        # Sorting
        sort = self.request.GET.get('sort', 'symbol')
        if sort in ['symbol', 'name', 'current_price', 'change_percent']:
            queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['sort'] = self.request.GET.get('sort', 'symbol')
        return context

class StockDetailView(LoginRequiredMixin, DetailView):
    model = Stock
    template_name = 'core/stock_detail.html'
    context_object_name = 'stock'
    
    def get_object(self, queryset=None):
        return get_object_or_404(Stock, symbol=self.kwargs['symbol'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stock = self.get_object()
        
        # Track view
        ChartView.objects.create(user=self.request.user, stock=stock)
        
        # Get user's portfolios for the quick add form
        context['portfolios'] = Portfolio.objects.filter(user=self.request.user)
        
        # Get holdings in this stock
        context['user_holdings'] = Holding.objects.filter(
            portfolio__user=self.request.user,
            stock=stock
        )
        
        # Generate historical data for chart (mock data for demo)
        import random
        
        dates = [(datetime.now() - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(30, 0, -1)]
        base_price = float(stock.current_price)
        prices = [base_price * (0.9 + (i/100) + (random.random() - 0.5) * 0.1) for i in range(30)]
        
        context['chart_labels'] = json.dumps(dates)
        context['chart_prices'] = json.dumps(prices)
        
        return context
class RegisterView(CreateView):
    form_class = CustomUserCreationForm  
    template_name = 'auth/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Create profile for user
        Profile.objects.create(user=self.object)
        messages.success(self.request, 'Account created successfully! Please login.')
        return response