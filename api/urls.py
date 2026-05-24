from django.urls import path
from .views import *

urlpatterns = [
    path('merchants/', MerchantListCreateView.as_view()),
    path('financing/', FinancingRequestCreateView.as_view()),
    path('lender/requests/', LenderRequestListView.as_view()),
]