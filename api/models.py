from django.db import models

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

    def __str__(self):
        return f"{self.merchant.name} - {self.amount}"