from django.urls import path
from . import views

urlpatterns = [
    path('merchants/', views.MerchantListCreateView.as_view(), name='merchant-list-create'),
    path('financing-requests/', views.FinancingRequestCreateView.as_view(), name='financing-request-create'),
    path('financing-requests/<int:pk>/', views.FinancingRequestDetailView.as_view(), name='financing-request-detail'),
    path('lender/requests/', views.LenderRequestListView.as_view(), name='lender-request-list'),
]