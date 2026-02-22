from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.PortfolioListView.as_view(), name='list'),
    path('create/', views.PortfolioCreateView.as_view(), name='create'),
    path('<int:pk>/', views.PortfolioDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.PortfolioUpdateView.as_view(), name='update'),
    path('<int:pk>/add-holding/', views.AddHoldingView.as_view(), name='add_holding'),
    path('holding/<int:pk>/update/', views.UpdateHoldingView.as_view(), name='update_holding'),
    path('holding/<int:pk>/delete/', views.DeleteHoldingView.as_view(), name='delete_holding'),
    path('chart/<int:stock_id>/', views.StockChartView.as_view(), name='stock_chart'),
]