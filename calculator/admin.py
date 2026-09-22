from django.contrib import admin

from .models import Calculation


@admin.register(Calculation)
class CalculationAdmin(admin.ModelAdmin):
    list_display = ("id", "expression", "result", "created_at")
    list_filter = ("created_at",)
    search_fields = ("expression",)
    readonly_fields = ("expression", "result", "created_at")
    ordering = ("-created_at",)
