from django.db import models


class Calculation(models.Model):
    """Stores a single calculator expression and its evaluated result."""

    expression = models.CharField(max_length=255)
    result = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.expression} = {self.result}"
