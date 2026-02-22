from django.contrib import admin
from .models import Portfolio, Holding, ChartView

class HoldingInline(admin.TabularInline):
    model = Holding
    extra = 1
    raw_id_fields = ('stock',)

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'total_value', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('name', 'user__email')
    inlines = [HoldingInline]
    readonly_fields = ('total_value',)

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'stock', 'quantity', 'average_buy_price', 'created_at')
    list_filter = ('portfolio__user', 'stock')
    search_fields = ('portfolio__name', 'stock__symbol')
    raw_id_fields = ('stock',)

@admin.register(ChartView)
class ChartViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'viewed_at')
    list_filter = ('viewed_at',)
    date_hierarchy = 'viewed_at'