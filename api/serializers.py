from rest_framework import serializers
from .models import Merchant, FinancingRequest

class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = '__all__'


class FinancingRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = FinancingRequest
        fields = '__all__'

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )
        return value