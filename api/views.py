from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Merchant, FinancingRequest, AuditLog, User
from .serializers import (
    MerchantSerializer,
    MerchantListSerializer,
    FinancingRequestSerializer,
    FinancingRequestStatusUpdateSerializer,
    AuditLogSerializer,
    UserCreateSerializer,
    UserSerializer,
    DashboardStatsSerializer
)
from .permissions import RoleBasedPermission, IsMerchantOwner

# ========== EXPORT RATE LIMITING ==========

class ExportRateThrottle(UserRateThrottle):
    """Rate limit for export endpoints (compliance control)"""
    rate = '10/hour'  # Limited exports per hour


# ========== AUTHENTICATION VIEWS ==========

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view with login audit logging"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Log successful login
        user = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        
        if user and response.status_code == 200:
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                resource_type='User',
                resource_id=user.id,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'login_time': str(timezone.now())}
            )
        
        return response


class StaffLoginView(APIView):
    """Session-based login for internal staff dashboard"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Only staff roles can access dashboard
            if user.role in ['admin', 'compliance', 'lender_partner', 'support']:
                login(request, user)
                
                # Log staff login
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    resource_type='User',
                    resource_id=user.id,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'login_time': str(timezone.now()), 'method': 'session'}
                )
                
                return Response({
                    "detail": "Logged in successfully",
                    "role": user.role,
                    "username": user.username
                })
            else:
                return Response(
                    {"detail": "Not authorized for staff access"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )


class StaffDashboardView(APIView):
    """Protected staff dashboard requiring session authentication"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Check if user has staff role
        if request.user.role not in ['admin', 'compliance', 'lender_partner', 'support']:
            return Response(
                {"detail": "Access denied. Staff only."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log dashboard access
        AuditLog.objects.create(
            user=request.user,
            action='VIEW_SENSITIVE',
            resource_type='Dashboard',
            resource_id=0,
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'dashboard_type': 'staff'}
        )
        
        # Role-based dashboard data
        dashboard_data = {
            "user": request.user.username,
            "role": request.user.role,
            "dashboard": "Staff Dashboard",
            "timestamp": str(timezone.now())
        }
        
        # Add role-specific data
        if request.user.role == 'admin':
            dashboard_data['total_merchants'] = Merchant.objects.count()
            dashboard_data['total_requests'] = FinancingRequest.objects.count()
            dashboard_data['pending_requests'] = FinancingRequest.objects.filter(status='pending').count()
        elif request.user.role == 'compliance':
            dashboard_data['audit_logs_count'] = AuditLog.objects.count()
            dashboard_data['recent_logs'] = AuditLog.objects.filter(
                timestamp__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
        elif request.user.role == 'lender_partner':
            assigned_merchants = request.user.assigned_merchants.all()
            dashboard_data['assigned_merchants_count'] = assigned_merchants.count()
            dashboard_data['pending_requests'] = FinancingRequest.objects.filter(
                merchant__in=assigned_merchants,
                status='pending'
            ).count()
        
        return Response(dashboard_data)


class UserRegistrationView(generics.CreateAPIView):
    """Public endpoint for user registration"""
    
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Log registration
        AuditLog.objects.create(
            user=user,
            action='CREATE',
            resource_type='User',
            resource_id=user.id,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={'role': user.role}
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for users to see and update their own profile"""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """Logout view (blacklists refresh token)"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log logout
            AuditLog.objects.create(
                user=request.user,
                action='LOGOUT',
                resource_type='User',
                resource_id=request.user.id,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ========== EXPORT CONTROLS VIEW ==========

class ExportDataView(APIView):
    """Export data with rate limiting for compliance"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ExportRateThrottle]
    
    def get(self, request):
        # Only admin and compliance can export data
        if request.user.role not in ['admin', 'compliance']:
            return Response(
                {"detail": "Access denied. Export requires admin or compliance role."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log the export (audit trail)
        AuditLog.objects.create(
            user=request.user,
            action='EXPORT',
            resource_type='Data',
            resource_id=0,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'export_type': 'merchant_data',
                'timestamp': str(timezone.now())
            }
        )
        
        # Prepare export data (role-based filtering)
        if request.user.role == 'admin':
            merchants = Merchant.objects.all().values('id', 'name', 'email', 'phone', 'business_type')
        else:  # compliance sees all but can't modify
            merchants = Merchant.objects.all().values('id', 'name', 'email', 'business_type')
        
        # Also export financing requests
        financing_requests = FinancingRequest.objects.all().values(
            'id', 'merchant__name', 'amount', 'purpose', 'status', 'created_at'
        )
        
        return Response({
            "exported_by": request.user.username,
            "exported_by_role": request.user.role,
            "exported_at": str(timezone.now()),
            "merchants": list(merchants),
            "financing_requests": list(financing_requests),
            "total_merchants": merchants.count(),
            "total_requests": financing_requests.count()
        })


# ========== MERCHANT VIEWS (WITH RBAC) ==========

class MerchantListCreateView(generics.ListCreateAPIView):
    """
    List all merchants or create a new merchant.
    - Admin/Compliance: Can see all merchants
    - Lender Partner: Can only see assigned merchants
    - Merchant: Can only see their own merchant profile
    - Support: Can see basic info (no sensitive data)
    """
    
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail"""
        if self.request.method == 'GET' and not self.request.query_params.get('detail'):
            return MerchantListSerializer
        return MerchantSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all
        if user.role == 'admin':
            return Merchant.objects.all()
        
        # Compliance sees all (read-only)
        if user.role == 'compliance':
            return Merchant.objects.all()
        
        # Lender partner sees assigned merchants only
        if user.role == 'lender_partner':
            return user.assigned_merchants.all()
        
        # Merchant sees own profile
        if user.role == 'merchant' and user.merchant_profile:
            return Merchant.objects.filter(owner=user)
        
        # Support sees all but with limited fields (handled by serializer)
        if user.role == 'support':
            return Merchant.objects.all()
        
        return Merchant.objects.none()
    
    def perform_create(self, serializer):
        """Create merchant and log the action"""
        merchant = serializer.save(created_by=self.request.user)
        
        # Log creation
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            resource_type='Merchant',
            resource_id=merchant.id,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={'merchant_name': merchant.name, 'business_type': merchant.business_type}
        )
        
        return merchant


class MerchantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific merchant.
    Object-level permissions ensure data-aware access control.
    """
    
    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'admin':
            return Merchant.objects.all()
        
        if user.role == 'compliance':
            return Merchant.objects.all()
        
        if user.role == 'lender_partner':
            return user.assigned_merchants.all()
        
        if user.role == 'merchant':
            return Merchant.objects.filter(owner=user)
        
        if user.role == 'support':
            return Merchant.objects.all()
        
        return Merchant.objects.none()
    
    def perform_update(self, serializer):
        """Update merchant and log changes"""
        old_name = self.get_object().name
        merchant = serializer.save()
        
        # Log update
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE',
            resource_type='Merchant',
            resource_id=merchant.id,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            details={
                'old_name': old_name,
                'new_name': merchant.name,
                'changes': list(serializer.validated_data.keys())
            }
        )
    
    def perform_destroy(self, instance):
        """Delete merchant and log action"""
        AuditLog.objects.create(
            user=self.request.user,
            action='DELETE',
            resource_type='Merchant',
            resource_id=instance.id,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            details={'merchant_name': instance.name}
        )
        instance.delete()


# ========== FINANCING REQUEST VIEWS (WITH RBAC) ==========

class FinancingRequestCreateView(generics.ListCreateAPIView):
    """
    List all financing requests or create a new one.
    - Admin/Compliance: See all requests
    - Lender Partner: See requests from assigned merchants only
    - Merchant: See only their own requests
    """
    
    serializer_class = FinancingRequestSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all
        if user.role == 'admin':
            return FinancingRequest.objects.all().order_by('-created_at')
        
        # Compliance sees all (read-only)
        if user.role == 'compliance':
            return FinancingRequest.objects.all().order_by('-created_at')
        
        # Lender partner sees assigned merchants' requests
        if user.role == 'lender_partner':
            assigned_merchants = user.assigned_merchants.all()
            return FinancingRequest.objects.filter(
                merchant__in=assigned_merchants
            ).order_by('-created_at')
        
        # Merchant sees own requests
        if user.role == 'merchant' and user.merchant_profile:
            return FinancingRequest.objects.filter(
                merchant=user.merchant_profile
            ).order_by('-created_at')
        
        # Support sees all but with limited access (handled by permission)
        if user.role == 'support':
            return FinancingRequest.objects.all().order_by('-created_at')
        
        return FinancingRequest.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Override create to handle merchant assignment"""
        # Make a mutable copy of the data
        data = request.data.copy()
        
        # If user is a merchant, automatically set their merchant profile
        if request.user.role == 'merchant' and request.user.merchant_profile:
            data['merchant'] = request.user.merchant_profile.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Create financing request"""
        financing = serializer.save(created_by=self.request.user)
        # Alert functionality disabled (requires Redis/Celery)
        # The original async alert from Formative 1 is preserved in tasks.py
        return financing


class FinancingRequestDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update a single financing request.
    Updates will trigger the async alert via post_save signal.
    Object-level permissions ensure data-aware access control.
    """
    
    serializer_class = FinancingRequestSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'admin':
            return FinancingRequest.objects.all()
        
        if user.role == 'compliance':
            return FinancingRequest.objects.all()
        
        if user.role == 'lender_partner':
            assigned_merchants = user.assigned_merchants.all()
            return FinancingRequest.objects.filter(merchant__in=assigned_merchants)
        
        if user.role == 'merchant' and user.merchant_profile:
            return FinancingRequest.objects.filter(merchant=user.merchant_profile)
        
        if user.role == 'support':
            return FinancingRequest.objects.all()
        
        return FinancingRequest.objects.none()
    
    def perform_update(self, serializer):
        """Update financing request"""
        financing = serializer.save()
        # Alert functionality disabled (requires Redis/Celery)
        return financing


class FinancingRequestStatusUpdateView(generics.UpdateAPIView):
    """
    Specialized view for approving/rejecting financing requests.
    Only lender partners, compliance, and admin can change status.
    """
    
    serializer_class = FinancingRequestStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Only users who can approve/reject
        if user.role in ['admin', 'compliance', 'lender_partner']:
            if user.role == 'lender_partner':
                assigned_merchants = user.assigned_merchants.all()
                return FinancingRequest.objects.filter(merchant__in=assigned_merchants)
            return FinancingRequest.objects.all()
        
        return FinancingRequest.objects.none()
    
    def perform_update(self, serializer):
        financing = serializer.save()
        # Alert functionality disabled (requires Redis/Celery)
        return financing


class LenderRequestListView(generics.ListAPIView):
    """
    View for lenders to see all financing requests.
    Updated with proper RBAC filtering.
    """
    
    serializer_class = FinancingRequestSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        user = self.request.user
        
        # Only lenders, compliance, and admin can use this view
        if user.role == 'lender_partner':
            assigned_merchants = user.assigned_merchants.all()
            return FinancingRequest.objects.filter(
                merchant__in=assigned_merchants
            ).order_by('-created_at')
        
        if user.role in ['compliance', 'admin']:
            return FinancingRequest.objects.all().order_by('-created_at')
        
        # Return empty for unauthorized roles
        return FinancingRequest.objects.none()


# ========== AUDIT LOG VIEW (COMPLIANCE ONLY) ==========

class AuditLogListView(generics.ListAPIView):
    """
    View for accessing audit logs.
    Only accessible by compliance officers and admins.
    """
    
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Only compliance and admin can view audit logs
        if user.role not in ['compliance', 'admin']:
            return AuditLog.objects.none()
        
        queryset = AuditLog.objects.all()
        
        # Filter by query parameters
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset[:500]  # Limit to last 500 logs for performance


# ========== DASHBOARD STATS VIEW (ROLE-BASED) ==========

class DashboardStatsView(APIView):
    """
    Get dashboard statistics based on user role.
    Shows different data for different roles.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        stats = {}
        
        # Common stats
        stats['user_role'] = user.role
        
        if user.role == 'admin':
            # Full system stats
            stats['total_merchants'] = Merchant.objects.count()
            stats['total_financing_requests'] = FinancingRequest.objects.count()
            stats['pending_requests'] = FinancingRequest.objects.filter(status='pending').count()
            stats['approved_requests'] = FinancingRequest.objects.filter(status='approved').count()
            stats['rejected_requests'] = FinancingRequest.objects.filter(status='rejected').count()
            stats['total_amount_pending'] = FinancingRequest.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
            stats['total_amount_approved'] = FinancingRequest.objects.filter(status='approved').aggregate(Sum('amount'))['amount__sum'] or 0
            stats['recent_audit_logs'] = AuditLog.objects.count()
        
        elif user.role == 'compliance':
            # Compliance sees all but with focus on audit
            stats['total_merchants'] = Merchant.objects.count()
            stats['total_financing_requests'] = FinancingRequest.objects.count()
            stats['pending_requests'] = FinancingRequest.objects.filter(status='pending').count()
            stats['approved_requests'] = FinancingRequest.objects.filter(status='approved').count()
            stats['rejected_requests'] = FinancingRequest.objects.filter(status='rejected').count()
            stats['audit_logs_7days'] = AuditLog.objects.filter(timestamp__gte=timezone.now() - timezone.timedelta(days=7)).count()
        
        elif user.role == 'lender_partner':
            # Lender sees only assigned merchants
            assigned_merchants = user.assigned_merchants.all()
            stats['assigned_merchants_count'] = assigned_merchants.count()
            stats['total_requests'] = FinancingRequest.objects.filter(merchant__in=assigned_merchants).count()
            stats['pending_requests'] = FinancingRequest.objects.filter(merchant__in=assigned_merchants, status='pending').count()
            stats['approved_requests'] = FinancingRequest.objects.filter(merchant__in=assigned_merchants, status='approved').count()
            stats['total_amount_pending'] = FinancingRequest.objects.filter(merchant__in=assigned_merchants, status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
        
        elif user.role == 'merchant' and user.merchant_profile:
            # Merchant sees only their own stats
            merchant = user.merchant_profile
            stats['merchant_name'] = merchant.name
            stats['my_requests'] = FinancingRequest.objects.filter(merchant=merchant).count()
            stats['pending_requests'] = FinancingRequest.objects.filter(merchant=merchant, status='pending').count()
            stats['approved_requests'] = FinancingRequest.objects.filter(merchant=merchant, status='approved').count()
            stats['total_amount_requested'] = FinancingRequest.objects.filter(merchant=merchant).aggregate(Sum('amount'))['amount__sum'] or 0
        
        elif user.role == 'support':
            # Support sees basic counts only
            stats['total_merchants'] = Merchant.objects.count()
            stats['active_requests'] = FinancingRequest.objects.exclude(status='rejected').count()
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)