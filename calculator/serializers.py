from rest_framework import serializers

from .models import Calculation


class CalculationSerializer(serializers.ModelSerializer):
    """Serialize Calculation records for API responses."""

    class Meta:
        model = Calculation
        fields = ["id", "expression", "result", "created_at"]
        read_only_fields = ["id", "expression", "result", "created_at"]


class CalculateRequestSerializer(serializers.Serializer):
    """Validate the calculate endpoint request body."""

    expression = serializers.CharField(required=True, allow_blank=False, max_length=255)
