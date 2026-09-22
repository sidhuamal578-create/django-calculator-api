from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Calculation
from .serializers import CalculateRequestSerializer, CalculationSerializer
from .services import CalculatorError, evaluate_expression


def error_response(code, message, http_status):
    """Build a consistent error payload for the React frontend."""
    return Response(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
        status=http_status,
    )


def success_response(data=None, message=None, http_status=status.HTTP_200_OK):
    """Build a consistent success payload for the React frontend."""
    payload = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return Response(payload, status=http_status)


class ApiRootView(APIView):
    """GET /api/ — API discovery for browsers and frontend developers."""

    def get(self, request):
        return success_response(
            data={
                "message": "Calculator Backend API is running.",
                "base_url": "/api/",
                "endpoints": [
                    {
                        "method": "POST",
                        "path": "/api/calculate/",
                        "description": "Evaluate a mathematical expression and store it.",
                    },
                    {
                        "method": "GET",
                        "path": "/api/history/",
                        "description": "List calculation history (newest first).",
                    },
                    {
                        "method": "GET",
                        "path": "/api/history/<id>/",
                        "description": "Get a single calculation by id.",
                    },
                    {
                        "method": "DELETE",
                        "path": "/api/history/<id>/",
                        "description": "Delete a single calculation by id.",
                    },
                    {
                        "method": "DELETE",
                        "path": "/api/history/clear/",
                        "description": "Clear all calculation history.",
                    },
                ],
            }
        )


class CalculateView(APIView):
    """POST /api/calculate/ — evaluate an expression and store it."""

    def post(self, request):
        request_serializer = CalculateRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return error_response(
                "INVALID_EXPRESSION",
                "Expression is required and cannot be empty.",
                status.HTTP_400_BAD_REQUEST,
            )

        expression = request_serializer.validated_data["expression"]

        try:
            result = evaluate_expression(expression)
        except CalculatorError as exc:
            return error_response(exc.code, exc.message, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(
                "SERVER_ERROR",
                "An unexpected error occurred while evaluating the expression.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        calculation = Calculation.objects.create(
            expression=expression.strip(),
            result=result,
        )

        return success_response(
            data=CalculationSerializer(calculation).data,
            http_status=status.HTTP_201_CREATED,
        )


class HistoryListView(APIView):
    """GET /api/history/ — return all calculations, newest first."""

    def get(self, request):
        calculations = Calculation.objects.all()
        serializer = CalculationSerializer(calculations, many=True)
        return success_response(data=serializer.data)


class HistoryDetailView(APIView):
    """GET/DELETE /api/history/<id>/ — retrieve or delete one calculation."""

    def get(self, request, pk):
        try:
            calculation = Calculation.objects.get(pk=pk)
        except Calculation.DoesNotExist:
            return error_response(
                "NOT_FOUND",
                "Calculation not found.",
                status.HTTP_404_NOT_FOUND,
            )

        return success_response(data=CalculationSerializer(calculation).data)

    def delete(self, request, pk):
        try:
            calculation = Calculation.objects.get(pk=pk)
        except Calculation.DoesNotExist:
            return error_response(
                "NOT_FOUND",
                "Calculation not found.",
                status.HTTP_404_NOT_FOUND,
            )

        calculation.delete()
        return success_response(message="Calculation deleted successfully.")


class HistoryClearView(APIView):
    """DELETE /api/history/clear/ — delete all calculation history."""

    def delete(self, request):
        Calculation.objects.all().delete()
        return success_response(
            message="Calculation history cleared successfully.",
        )
