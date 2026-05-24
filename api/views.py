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

        send_alert.delay(financing.id)

class LenderRequestListView(generics.ListAPIView):
    queryset = FinancingRequest.objects.all().order_by('-created_at')
    serializer_class = FinancingRequestSerializer