from django.urls import path

from .views import (
    ApiRootView,
    CalculateView,
    HistoryClearView,
    HistoryDetailView,
    HistoryListView,
)

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("calculate/", CalculateView.as_view(), name="calculate"),
    path("history/clear/", HistoryClearView.as_view(), name="history-clear"),
    path("history/", HistoryListView.as_view(), name="history-list"),
    path("history/<int:pk>/", HistoryDetailView.as_view(), name="history-detail"),
]
