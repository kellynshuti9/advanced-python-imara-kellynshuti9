from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    """
    Permission class that checks user role for access control.
    Combined with object-level checks for data-aware access.
    """
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can do everything
        if request.user.role == 'admin':
            return True
        
        # Support can only read (GET, HEAD, OPTIONS)
        if request.user.role == 'support':
            return request.method in permissions.SAFE_METHODS
        
        # Compliance can read everything but not modify
        if request.user.role == 'compliance':
            return request.method in permissions.SAFE_METHODS
        
        # Lender partners can read and update (but object-level will restrict)
        if request.user.role == 'lender_partner':
            return True
        
        # Merchants can read and create
        if request.user.role == 'merchant':
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Object-level permissions for data-aware access"""
        
        # Admin can access any object
        if request.user.role == 'admin':
            return True
        
        # Compliance can read any object but not modify
        if request.user.role == 'compliance':
            return request.method in permissions.SAFE_METHODS
        
        # Support cannot access objects directly (list view only)
        if request.user.role == 'support':
            return False
        
        # Check merchant ownership
        if request.user.role == 'merchant':
            # For Merchant objects
            if hasattr(obj, 'owner'):
                return obj.owner == request.user
            # For FinancingRequest objects
            if hasattr(obj, 'merchant') and hasattr(obj.merchant, 'owner'):
                return obj.merchant.owner == request.user
        
        # Check lender partner assignment
        if request.user.role == 'lender_partner':
            if hasattr(obj, 'merchant'):
                merchant = obj.merchant
            elif hasattr(obj, 'owner'):
                merchant = obj
            else:
                return False
            
            return merchant in request.user.assigned_merchants.all()
        
        return False


class IsMerchantOwner(permissions.BasePermission):
    """Specifically for checking merchant ownership"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.role != 'merchant':
            return False
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        if hasattr(obj, 'merchant') and hasattr(obj.merchant, 'owner'):
            return obj.merchant.owner == request.user
        
        return False


class IsLenderOrAdmin(permissions.BasePermission):
    """For lender-specific operations"""
    
    def has_permission(self, request, view):
        return request.user.role in ['lender_partner', 'admin', 'compliance']