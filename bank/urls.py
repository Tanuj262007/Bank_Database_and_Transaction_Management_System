from django.urls import path
from bank import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('deposit/', views.deposit, name='deposit'),
    path('transfer/', views.transfer, name='transfer'),
    path('transactions/', views.transactions, name='transactions'),
    path('loans/', views.loans, name='loans'),
    path(
    'beneficiaries/',
    views.beneficiaries,
    name='beneficiaries'
),
]