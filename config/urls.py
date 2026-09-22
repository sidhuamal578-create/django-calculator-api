from django.contrib import admin
from django.urls import include, path
from rest_framework.response import Response
from rest_framework.views import APIView


class RootView(APIView):
    """GET / — point visitors to the API base URL."""

    def get(self, request):
        return Response(
            {
                "success": True,
                "data": {
                    "message": "Calculator Backend is running.",
                    "api_base_url": "/api/",
                    "docs": "See README.md for full API documentation.",
                },
            }
        )


urlpatterns = [
    path("", RootView.as_view(), name="root"),
    path("admin/", admin.site.urls),
    path("api/", include("calculator.urls")),
]
