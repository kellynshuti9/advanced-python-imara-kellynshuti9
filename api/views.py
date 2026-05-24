from rest_framework import generics
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


class LenderRequestListView(generics.ListAPIView):
    queryset = FinancingRequest.objects.all().order_by('-created_at')
    serializer_class = FinancingRequestSerializer