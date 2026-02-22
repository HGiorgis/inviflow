from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, Stock

class Portfolio(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100, default='Main Portfolio')
    description = models.TextField(blank=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.email}'s {self.name}"
    
    def update_total_value(self):
        total = self.holdings.aggregate(
            total=models.Sum(models.F('quantity') * models.F('stock__current_price'))
        )['total'] or 0
        self.total_value = total
        self.save()

class Holding(TimeStampedModel):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='holdings')
    quantity = models.DecimalField(max_digits=15, decimal_places=4)
    average_buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['portfolio', 'stock']
    
    def __str__(self):
        return f"{self.portfolio} - {self.stock.symbol}: {self.quantity}"
    
    @property
    def current_value(self):
        return self.quantity * self.stock.current_price
    
    @property
    def profit_loss(self):
        return (self.stock.current_price - self.average_buy_price) * self.quantity
    
    @property
    def profit_loss_percent(self):
        if self.average_buy_price:
            return ((self.stock.current_price - self.average_buy_price) / self.average_buy_price) * 100
        return 0

class ChartView(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chart_views')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='chart_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']