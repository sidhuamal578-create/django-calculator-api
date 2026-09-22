from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Calculation
from .services import CalculatorError, evaluate_expression


class ApiRootTests(TestCase):
    """API discovery endpoints should respond with 200 JSON."""

    def setUp(self):
        self.client = APIClient()

    def test_api_root(self):
        response = self.client.get(reverse("api-root"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("endpoints", response.data["data"])
        self.assertGreaterEqual(len(response.data["data"]["endpoints"]), 5)

    def test_project_root(self):
        response = self.client.get(reverse("root"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["api_base_url"], "/api/")


class EvaluateExpressionTests(TestCase):
    """Unit tests for the safe calculator service."""

    def test_addition(self):
        self.assertEqual(evaluate_expression("2 + 3"), 5.0)

    def test_subtraction(self):
        self.assertEqual(evaluate_expression("10 - 4"), 6.0)

    def test_multiplication(self):
        self.assertEqual(evaluate_expression("5 * 6"), 30.0)

    def test_division(self):
        self.assertEqual(evaluate_expression("100 / 4"), 25.0)

    def test_decimal(self):
        self.assertEqual(evaluate_expression("10.5 + 2.5"), 13.0)

    def test_parentheses(self):
        self.assertEqual(evaluate_expression("(10 + 5) * 2"), 30.0)

    def test_operator_precedence(self):
        self.assertEqual(evaluate_expression("2 + 3 * 4"), 14.0)
        self.assertEqual(evaluate_expression("25 + 10 * 2"), 45.0)

    def test_negative_numbers(self):
        self.assertEqual(evaluate_expression("-5 + 3"), -2.0)
        self.assertEqual(evaluate_expression("10 + -2"), 8.0)
        self.assertEqual(evaluate_expression("-(2 + 3)"), -5.0)

    def test_invalid_expression(self):
        with self.assertRaises(CalculatorError) as ctx:
            evaluate_expression("10 +")
        self.assertEqual(ctx.exception.code, "INVALID_EXPRESSION")

    def test_invalid_characters(self):
        with self.assertRaises(CalculatorError) as ctx:
            evaluate_expression("2 ^ 3")
        self.assertEqual(ctx.exception.code, "INVALID_EXPRESSION")

    def test_division_by_zero(self):
        with self.assertRaises(CalculatorError) as ctx:
            evaluate_expression("10 / 0")
        self.assertEqual(ctx.exception.code, "DIVISION_BY_ZERO")

    def test_malicious_import(self):
        with self.assertRaises(CalculatorError):
            evaluate_expression('__import__("os").system("echo hacked")')

    def test_malicious_name(self):
        with self.assertRaises(CalculatorError):
            evaluate_expression("import os")

    def test_malicious_builtins(self):
        for payload in (
            "open('x')",
            "exec('1')",
            "globals()",
            "locals()",
            "subprocess.call('ls')",
        ):
            with self.assertRaises(CalculatorError):
                evaluate_expression(payload)

    def test_empty_expression(self):
        with self.assertRaises(CalculatorError) as ctx:
            evaluate_expression("   ")
        self.assertEqual(ctx.exception.code, "INVALID_EXPRESSION")

    def test_expression_too_long(self):
        with self.assertRaises(CalculatorError) as ctx:
            evaluate_expression("1+" * 200)
        self.assertEqual(ctx.exception.code, "INVALID_EXPRESSION")


class CalculateAPITests(TestCase):
    """API tests for POST /api/calculate/."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("calculate")

    def test_successful_calculation(self):
        response = self.client.post(
            self.url,
            {"expression": "25 + 10 * 2"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["expression"], "25 + 10 * 2")
        self.assertEqual(data["result"], 45.0)
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertEqual(Calculation.objects.count(), 1)

    def test_addition(self):
        response = self.client.post(self.url, {"expression": "10 + 5"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["result"], 15.0)

    def test_subtraction(self):
        response = self.client.post(self.url, {"expression": "20 - 8"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["result"], 12.0)

    def test_multiplication(self):
        response = self.client.post(self.url, {"expression": "7 * 6"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["result"], 42.0)

    def test_division(self):
        response = self.client.post(self.url, {"expression": "100 / 4"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["result"], 25.0)

    def test_decimal_calculation(self):
        response = self.client.post(
            self.url, {"expression": "10.5 + 2.5"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["result"], 13.0)

    def test_parentheses(self):
        response = self.client.post(
            self.url, {"expression": "(10 + 5) * 2"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["result"], 30.0)

    def test_negative_numbers(self):
        response = self.client.post(self.url, {"expression": "-5 + 10"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["result"], 5.0)

    def test_invalid_expression(self):
        response = self.client.post(self.url, {"expression": "10 +"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "INVALID_EXPRESSION")

    def test_division_by_zero(self):
        response = self.client.post(self.url, {"expression": "10 / 0"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "DIVISION_BY_ZERO")

    def test_malicious_expression_rejected(self):
        response = self.client.post(
            self.url,
            {"expression": '__import__("os").system("echo hacked")'},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(Calculation.objects.count(), 0)

    def test_missing_expression(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_empty_expression(self):
        response = self.client.post(self.url, {"expression": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_wrong_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "METHOD_NOT_ALLOWED")


class HistoryAPITests(TestCase):
    """API tests for history list, detail, delete, and clear."""

    def setUp(self):
        self.client = APIClient()
        self.first = Calculation.objects.create(expression="1 + 1", result=2.0)
        self.second = Calculation.objects.create(expression="2 * 3", result=6.0)

    def test_calculation_history(self):
        response = self.client.get(reverse("history-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], self.second.id)
        self.assertEqual(data[1]["id"], self.first.id)

    def test_get_single_calculation(self):
        response = self.client.get(
            reverse("history-detail", kwargs={"pk": self.first.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["expression"], "1 + 1")
        self.assertEqual(response.data["data"]["result"], 2.0)

    def test_get_single_calculation_not_found(self):
        response = self.client.get(reverse("history-detail", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "NOT_FOUND")

    def test_delete_calculation(self):
        response = self.client.delete(
            reverse("history-detail", kwargs={"pk": self.first.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["message"],
            "Calculation deleted successfully.",
        )
        self.assertFalse(Calculation.objects.filter(pk=self.first.id).exists())
        self.assertEqual(Calculation.objects.count(), 1)

    def test_delete_calculation_not_found(self):
        response = self.client.delete(reverse("history-detail", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])

    def test_clear_history(self):
        response = self.client.delete(reverse("history-clear"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["message"],
            "Calculation history cleared successfully.",
        )
        self.assertEqual(Calculation.objects.count(), 0)


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
)
class CorsAPITests(TestCase):
    """Verify CORS allowlist for React development origins."""

    def setUp(self):
        self.client = APIClient()

    def test_cors_allows_vite_origin(self):
        response = self.client.post(
            reverse("calculate"),
            {"expression": "1 + 1"},
            format="json",
            HTTP_ORIGIN="http://localhost:5173",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:5173",
        )

    def test_cors_allows_cra_origin(self):
        response = self.client.get(
            reverse("history-list"),
            HTTP_ORIGIN="http://localhost:3000",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:3000",
        )

    def test_cors_blocks_unknown_origin(self):
        response = self.client.get(
            reverse("history-list"),
            HTTP_ORIGIN="http://evil.example",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
