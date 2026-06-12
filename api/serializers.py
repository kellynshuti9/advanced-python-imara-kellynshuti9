from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Merchant, FinancingRequest, AuditLog
from .encryption import decrypt_sensitive_data, encrypt_sensitive_data, get_tax_id_last4

User = get_user_model()

# ========== USER SERIALIZERS ==========
class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer - used for displaying user info"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_display', 'phone']
        read_only_fields = ['id']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users with password hashing"""
    
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'role', 'phone']
    
    def validate(self, data):
        """Check that passwords match"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data
    
    def validate_role(self, value):
        """Validate role is allowed for self-registration"""
        # Regular users can only register as merchant or lender partner
        # Admin/compliance accounts must be created via admin panel
        if value not in ['merchant', 'lender_partner']:
            raise serializers.ValidationError("You can only register as merchant or lender partner")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password - NO merchant creation here"""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # IMPORTANT: Do NOT create merchant profile here
        # The signal in models.py handles this automatically
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (non-password changes)"""
    
    class Meta:
        model = User
        fields = ['email', 'phone']
        read_only_fields = ['username', 'role']


# ========== MERCHANT SERIALIZER WITH PRIVACY CONTROLS ==========
class MerchantSerializer(serializers.ModelSerializer):
    """Merchant serializer with role-based field visibility and encryption"""
    
    # Read-only fields that are computed
    tax_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    account_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Display fields (role-dependent)
    tax_id_display = serializers.SerializerMethodField(read_only=True)
    account_number_display = serializers.SerializerMethodField(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True, default=None)
    
    class Meta:
        model = Merchant
        fields = [
            'id', 'name', 'email', 'phone', 'business_type', 
            'created_at', 'updated_at', 'owner', 'owner_username',
            'tax_id', 'tax_id_display', 'account_number', 'account_number_display'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_tax_id_display(self, obj):
        """Return tax ID based on requesting user's role"""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return None
        
        user = request.user
        
        # Full access for admin and compliance
        if user.role in ['admin', 'compliance']:
            return obj.tax_id  # This calls the property that decrypts
        
        # Partial access for owner merchant
        if user.role == 'merchant' and user.merchant_profile == obj:
            return f"***-{obj.tax_id_last4}" if obj.tax_id_last4 else None
        
        # No access for others
        return None
    
    def get_account_number_display(self, obj):
        """Return account number based on requesting user's role"""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return None
        
        user = request.user
        
        # Only admin and compliance can see full account numbers
        if user.role in ['admin', 'compliance']:
            return obj.account_number
        
        # Hide from everyone else (even owner for security)
        return None
    
    def validate_email(self, value):
        """Validate email format"""
        if value and '@' not in value:
            raise serializers.ValidationError("Enter a valid email address")
        return value
    
    def create(self, validated_data):
        """Create merchant with encrypted sensitive fields"""
        tax_id = validated_data.pop('tax_id', None)
        account_number = validated_data.pop('account_number', None)
        
        merchant = super().create(validated_data)
        
        # Encrypt sensitive data if provided
        if tax_id:
            merchant.tax_id = tax_id  # Using the setter which encrypts
        if account_number:
            merchant.account_number = account_number  # Using the setter which encrypts
        
        merchant.save()
        return merchant
    
    def update(self, instance, validated_data):
        """Update merchant with encrypted sensitive fields"""
        tax_id = validated_data.pop('tax_id', None)
        account_number = validated_data.pop('account_number', None)
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update encrypted fields if provided
        if tax_id:
            instance.tax_id = tax_id
        if account_number:
            instance.account_number = account_number
        
        instance.save()
        return instance


class MerchantListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views (less data)"""
    
    class Meta:
        model = Merchant
        fields = ['id', 'name', 'email', 'business_type', 'created_at']
        read_only_fields = ['id', 'name', 'email', 'business_type', 'created_at']


# ========== FINANCING REQUEST SERIALIZER (ENHANCED) ==========
class FinancingRequestSerializer(serializers.ModelSerializer):
    """Financing request serializer with audit trail and status workflow"""
    
    merchant_name = serializers.CharField(source='merchant.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, default=None)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FinancingRequest
        fields = [
            'id', 'merchant', 'merchant_name', 'amount', 'purpose', 
            'status', 'status_display', 'created_at', 'updated_at',
            'created_by', 'created_by_username', 'approved_by', 'approved_by_username',
            'approved_at', 'rejection_reason'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 
                           'approved_by', 'approved_at']
    
    def validate_amount(self, value):
        """YOUR ORIGINAL VALIDATION - KEPT AS IS"""
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )
        # Additional validation: reasonable amount limits
        if value > 1000000:
            raise serializers.ValidationError(
                "Amount exceeds maximum allowed ($1,000,000)"
            )
        return value
    
    def validate_purpose(self, value):
        """Validate purpose is not empty"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Please provide a detailed purpose (minimum 10 characters)"
            )
        return value
    
    def create(self, validated_data):
        """Create financing request with audit trail"""
        request = self.context.get('request')
        
        # Set the created_by to current user
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        financing_request = super().create(validated_data)
        
        # Log the creation in audit log
        from .models import AuditLog
        AuditLog.objects.create(
            user=request.user if request else None,
            action='CREATE',
            resource_type='FinancingRequest',
            resource_id=financing_request.id,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            details={
                'merchant_id': financing_request.merchant.id,
                'amount': str(financing_request.amount),
                'purpose_preview': financing_request.purpose[:50]
            }
        )
        
        return financing_request
    
    def update(self, instance, validated_data):
        """Update financing request with audit trail and approval logic"""
        request = self.context.get('request')
        old_status = instance.status
        
        # Check if this is an approval/rejection
        new_status = validated_data.get('status', instance.status)
        
        # If status changed to approved/rejected, set approval info
        if new_status != old_status and new_status in ['approved', 'rejected']:
            from django.utils import timezone
            validated_data['approved_by'] = request.user if request else None
            validated_data['approved_at'] = timezone.now()
            
            # If rejected, ensure rejection reason is provided
            if new_status == 'rejected' and not validated_data.get('rejection_reason'):
                raise serializers.ValidationError(
                    {"rejection_reason": "Rejection reason is required when rejecting a request"}
                )
        
        financing_request = super().update(instance, validated_data)
        
        # Log the update in audit log
        from .models import AuditLog
        AuditLog.objects.create(
            user=request.user if request else None,
            action='UPDATE',
            resource_type='FinancingRequest',
            resource_id=financing_request.id,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            details={
                'old_status': old_status,
                'new_status': financing_request.status,
                'changed_fields': list(validated_data.keys())
            }
        )
        
        return financing_request


class FinancingRequestStatusUpdateSerializer(serializers.ModelSerializer):
    """Specialized serializer for just updating status (approve/reject)"""
    
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = FinancingRequest
        fields = ['status', 'rejection_reason']
    
    def validate(self, data):
        """Validate status change rules"""
        status = data.get('status')
        rejection_reason = data.get('rejection_reason', '')
        
        if status == 'rejected' and not rejection_reason:
            raise serializers.ValidationError({
                "rejection_reason": "Rejection reason is required when rejecting"
            })
        
        return data
    
    def update(self, instance, validated_data):
        """Update status with proper audit trail"""
        from django.utils import timezone
        
        old_status = instance.status
        new_status = validated_data.get('status', instance.status)
        
        instance.status = new_status
        
        if new_status in ['approved', 'rejected']:
            instance.approved_by = self.context['request'].user
            instance.approved_at = timezone.now()
            
            if new_status == 'rejected':
                instance.rejection_reason = validated_data.get('rejection_reason', '')
        
        instance.save()
        
        # Log the status change
        from .models import AuditLog
        AuditLog.objects.create(
            user=self.context['request'].user,
            action='UPDATE',
            resource_type='FinancingRequest',
            resource_id=instance.id,
            details={
                'old_status': old_status,
                'new_status': new_status,
                'action': 'approve' if new_status == 'approved' else 'reject'
            }
        )
        
        return instance


# ========== AUDIT LOG SERIALIZER ==========
class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log entries (read-only)"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'username', 'user_role', 'action', 'action_display',
            'resource_type', 'resource_id', 'ip_address', 'timestamp', 'details'
        ]
        read_only_fields = ['id', 'username', 'user_role', 'action', 'action_display',
                           'resource_type', 'resource_id', 'ip_address', 'timestamp', 'details']


# ========== DASHBOARD STATS SERIALIZER ==========
class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics (role-based)"""
    
    total_merchants = serializers.IntegerField(required=False, default=0)
    total_financing_requests = serializers.IntegerField(required=False, default=0)
    pending_requests = serializers.IntegerField(required=False, default=0)
    approved_requests = serializers.IntegerField(required=False, default=0)
    rejected_requests = serializers.IntegerField(required=False, default=0)
    total_amount_pending = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0)
    total_amount_approved = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, default=0)
    user_role = serializers.CharField(required=False, default='')
    merchant_name = serializers.CharField(required=False, default='')
    my_requests = serializers.IntegerField(required=False, default=0)
    assigned_merchants_count = serializers.IntegerField(required=False, default=0)
    total_requests = serializers.IntegerField(required=False, default=0)
    audit_logs_7days = serializers.IntegerField(required=False, default=0)
    recent_audit_logs = serializers.IntegerField(required=False, default=0)
    active_requests = serializers.IntegerField(required=False, default=0)