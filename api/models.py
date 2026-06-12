from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from cryptography.fernet import Fernet
from django.conf import settings
import os

# ========== ENCRYPTION HELPER FUNCTIONS ==========
def get_cipher():
    """Get encryption cipher using key from settings"""
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if not key:
        # Generate a key for development (in production, always set in settings)
        key = Fernet.generate_key()
    return Fernet(key.encode() if isinstance(key, str) else key)

def encrypt_sensitive_data(value):
    """Encrypt sensitive data before storing"""
    if not value:
        return None
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def decrypt_sensitive_data(encrypted_value):
    """Decrypt sensitive data when accessing"""
    if not encrypted_value:
        return None
    cipher = get_cipher()
    return cipher.decrypt(encrypted_value.encode()).decode()

# ========== CUSTOM USER MODEL WITH ROLES ==========
class User(AbstractUser):
    """Extended user model with role-based access control"""
    
    ROLE_CHOICES = [
        ('merchant', 'Merchant'),
        ('lender_partner', 'Lender Partner'),
        ('compliance', 'Compliance Officer'),
        ('admin', 'Administrator'),
        ('support', 'Support Staff'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='merchant',
        help_text="User's role determines access permissions"
    )
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    
    # These will be set after merchant/lender creation
    merchant_profile = models.OneToOneField(
        'Merchant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profile',
        help_text="Link to merchant profile if role is merchant"
    )
    assigned_merchants = models.ManyToManyField(
        'Merchant',
        blank=True,
        related_name='assigned_lenders',
        help_text="Merchants assigned to this lender partner"
    )
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_merchant(self):
        return self.role == 'merchant'
    
    @property
    def is_lender(self):
        return self.role == 'lender_partner'
    
    @property
    def is_compliance(self):
        return self.role == 'compliance'
    
    @property
    def is_admin_user(self):
        return self.role == 'admin'
    
    @property
    def is_support(self):
        return self.role == 'support'

# ========== AUDIT LOG MODEL ==========
class AuditLog(models.Model):
    """Track all sensitive data access and important actions"""
    
    ACTION_CHOICES = [
        ('VIEW_SENSITIVE', 'Viewed Sensitive Data'),
        ('CREATE', 'Created Resource'),
        ('UPDATE', 'Updated Resource'),
        ('DELETE', 'Deleted Resource'),
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('EXPORT', 'Data Export'),
        ('ROLE_CHANGE', 'Role Changed'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50, help_text="Type of resource accessed (Merchant, FinancingRequest, etc.)")
    resource_id = models.IntegerField(help_text="ID of the resource accessed")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Browser/Client information")
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True, help_text="Additional context about the action")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

# ========== MERCHANT MODEL (ENHANCED) ==========
class Merchant(models.Model):
    BUSINESS_TYPES = [
        ('retail', 'Retail'),
        ('food', 'Food'),
        ('service', 'Service'),
    ]

    # Original fields (keep all existing)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW: Compliance fields
    owner = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_merchant',
        help_text="User who owns this merchant account"
    )
    
    # Encrypted sensitive fields (PII protection)
    tax_id_encrypted = models.TextField(
        blank=True, 
        null=True,
        help_text="Encrypted Tax ID / SSN"
    )
    account_number_encrypted = models.TextField(
        blank=True, 
        null=True,
        help_text="Encrypted Bank Account Number"
    )
    tax_id_last4 = models.CharField(
        max_length=4, 
        blank=True,
        help_text="Last 4 digits of tax ID for display purposes"
    )
    
    # Optional: Track who created/modified
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_merchants',
        help_text="User who created this merchant record"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("view_sensitive_merchant_data", "Can view encrypted merchant data"),
            ("export_merchant_data", "Can export merchant data"),
        ]
    
    def __str__(self):
        return self.name
    
    # Properties for safe access to encrypted data
    @property
    def tax_id(self):
        """Decrypt tax ID - only call after permission check!"""
        return decrypt_sensitive_data(self.tax_id_encrypted)
    
    @tax_id.setter
    def tax_id(self, value):
        """Encrypt tax ID before saving"""
        if value:
            self.tax_id_encrypted = encrypt_sensitive_data(value)
            self.tax_id_last4 = value[-4:] if len(value) >= 4 else value
        else:
            self.tax_id_encrypted = None
            self.tax_id_last4 = ''
    
    @property
    def account_number(self):
        """Decrypt account number - only call after permission check!"""
        return decrypt_sensitive_data(self.account_number_encrypted)
    
    @account_number.setter
    def account_number(self, value):
        """Encrypt account number before saving"""
        if value:
            self.account_number_encrypted = encrypt_sensitive_data(value)
        else:
            self.account_number_encrypted = None
    
    def get_public_data(self):
        """Return safe data that any authenticated user can see"""
        return {
            'id': self.id,
            'name': self.name,
            'business_type': self.business_type,
            'created_at': self.created_at,
        }
    
    def get_sensitive_data(self, requesting_user):
        """Return data based on requesting user's role"""
        data = self.get_public_data()
        data['email'] = self.email
        data['phone'] = self.phone
        
        # Role-based field visibility
        if requesting_user.role in ['admin', 'compliance']:
            # Full access
            data['tax_id'] = self.tax_id
            data['account_number'] = self.account_number
        elif requesting_user.role == 'merchant' and requesting_user.merchant_profile == self:
            # Partial access (own data)
            data['tax_id'] = f"***-{self.tax_id_last4}" if self.tax_id_last4 else None
            data['account_number'] = None  # Hide account number even from owner
        else:
            # No sensitive data for others
            data['tax_id'] = None
            data['account_number'] = None
        
        return data

# ========== FINANCING REQUEST MODEL (ENHANCED) ==========
class FinancingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Original fields
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW: Audit trail fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_financing_requests',
        help_text="User who created this request"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_financing_requests',
        help_text="User who approved/rejected this request"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason if rejected")
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("approve_financing_request", "Can approve financing requests"),
        ]
    
    def __str__(self):
        return f"{self.merchant.name} - ${self.amount} - {self.status}"
    
    def approve(self, approver):
        """Approve this financing request"""
        self.status = 'approved'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save()
        
        # Log the approval
        AuditLog.objects.create(
            user=approver,
            action='UPDATE',
            resource_type='FinancingRequest',
            resource_id=self.id,
            details={'action': 'approved', 'amount': str(self.amount)}
        )
    
    def reject(self, approver, reason):
        """Reject this financing request"""
        self.status = 'rejected'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        # Log the rejection
        AuditLog.objects.create(
            user=approver,
            action='UPDATE',
            resource_type='FinancingRequest',
            resource_id=self.id,
            details={'action': 'rejected', 'reason': reason}
        )

# ========== SIGNALS (Keep your existing, add new ones) ==========

# Your original signal - KEPT AS IS
@receiver(post_save, sender=FinancingRequest)
def trigger_alert_on_update(sender, instance, created, **kwargs):
    """Trigger async alert when an existing financing request is updated"""
    from .tasks import send_alert
    
    if not created:  # Only trigger on updates, not initial creation
        send_alert.delay(instance.id)

# NEW: Auto-create audit log for financing request creation
@receiver(post_save, sender=FinancingRequest)
def log_financing_request_creation(sender, instance, created, **kwargs):
    """Log when a financing request is created"""
    from django.utils import timezone
    
    if created:
        AuditLog.objects.create(
            user=instance.created_by,
            action='CREATE',
            resource_type='FinancingRequest',
            resource_id=instance.id,
            details={
                'merchant': instance.merchant.name,
                'amount': str(instance.amount),
                'purpose': instance.purpose[:100]  # Truncate for log
            }
        )

# NEW: Auto-create merchant profile when merchant user is created
@receiver(post_save, sender=User)
def create_merchant_profile_for_user(sender, instance, created, **kwargs):
    """Automatically create a merchant profile when a user with role='merchant' is created"""
    if created and instance.role == 'merchant' and not instance.merchant_profile:
        merchant = Merchant.objects.create(
            name=instance.username,
            email=instance.email,
            phone=instance.phone or '',
            business_type='retail',  # Default
            owner=instance,
            created_by=instance
        )
        instance.merchant_profile = merchant
        instance.save()