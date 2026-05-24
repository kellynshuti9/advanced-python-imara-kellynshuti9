from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Merchant(models.Model):
    BUSINESS_TYPES = [
        ('retail', 'Retail'),
        ('food', 'Food'),
        ('service', 'Service'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FinancingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.merchant.name} - {self.amount}"


# Signal to trigger alert when financing request is UPDATED
@receiver(post_save, sender=FinancingRequest)
def trigger_alert_on_update(sender, instance, created, **kwargs):
    """Trigger async alert when an existing financing request is updated"""
    from .tasks import send_alert
    
    if not created:  # Only trigger on updates, not initial creation
        send_alert.delay(instance.id)