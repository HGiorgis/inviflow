from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, Stock, StockHistory

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'change_percent', 'last_updated', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('symbol', 'name')
    readonly_fields = ('change_percent', 'last_updated')
    fieldsets = (
        (None, {
            'fields': ('symbol', 'name', 'is_active')
        }),
        ('Price Information', {
            'fields': ('current_price', 'previous_close', 'volume')
        }),
        ('Timestamps', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )

@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ('stock', 'price', 'date')
    list_filter = ('stock', 'date')
    date_hierarchy = 'date'