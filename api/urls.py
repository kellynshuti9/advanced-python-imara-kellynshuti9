from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # ========== JWT Authentication (API) ==========
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # ========== Session Authentication (Staff Dashboard) ==========
    path('staff/login/', views.StaffLoginView.as_view(), name='staff-login'),
    path('staff/dashboard/', views.StaffDashboardView.as_view(), name='staff-dashboard'),
    
    # ========== Export Controls (Compliance) ==========
    path('export/', views.ExportDataView.as_view(), name='export-data'),
    
    # ========== Merchants ==========
    path('merchants/', views.MerchantListCreateView.as_view(), name='merchant-list-create'),
    path('merchants/<int:pk>/', views.MerchantDetailView.as_view(), name='merchant-detail'),
    
    # ========== Financing Requests ==========
    path('financing-requests/', views.FinancingRequestCreateView.as_view(), name='financing-request-create'),
    path('financing-requests/<int:pk>/', views.FinancingRequestDetailView.as_view(), name='financing-request-detail'),
    path('financing-requests/<int:pk>/status/', views.FinancingRequestStatusUpdateView.as_view(), name='financing-request-status'),
    
    # ========== Lender Specific ==========
    path('lender/requests/', views.LenderRequestListView.as_view(), name='lender-request-list'),
    
    # ========== Audit (Compliance Only) ==========
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    
    # ========== Dashboard ==========
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
]