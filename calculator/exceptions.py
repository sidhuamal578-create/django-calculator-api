"""Consistent DRF exception handling for React-friendly JSON errors."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """
    Wrap DRF/Django exceptions in the project's standard error shape.

    Does not leak Python tracebacks or internal details to API clients.
    """
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "An unexpected server error occurred.",
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = "REQUEST_ERROR"
    message = "Request could not be completed."

    if response.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
        message = "Resource not found."
    elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        code = "METHOD_NOT_ALLOWED"
        message = "HTTP method not allowed for this endpoint."
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        code = "BAD_REQUEST"
        message = "Invalid request."
    elif response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE:
        code = "UNSUPPORTED_MEDIA_TYPE"
        message = "Content-Type must be application/json."

    response.data = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    return response
