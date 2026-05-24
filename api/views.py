from rest_framework import generics
from .tasks import send_alert
from .models import Merchant, FinancingRequest
from .serializers import (
    MerchantSerializer,
    FinancingRequestSerializer
)

class MerchantListCreateView(generics.ListCreateAPIView):
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer


class FinancingRequestCreateView(generics.ListCreateAPIView):
    queryset = FinancingRequest.objects.all()
    serializer_class = FinancingRequestSerializer

    def perform_create(self, serializer):
        financing = serializer.save()
        # Trigger alert on creation
        send_alert.delay(financing.id)


class FinancingRequestDetailView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating a single financing request.
    Updates will trigger the async alert via post_save signal.
    """
    queryset = FinancingRequest.objects.all()
    serializer_class = FinancingRequestSerializer
    # This supports both PUT (full update) and PATCH (partial update)


class LenderRequestListView(generics.ListAPIView):
    queryset = FinancingRequest.objects.all().order_by('-created_at')
    serializer_class = FinancingRequestSerializer