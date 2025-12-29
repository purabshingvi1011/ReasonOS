"""Tool executor for ReasonOS.

Executes tool calls and returns structured results.
"""

from typing import Any

from ..tools.calculator_tool import calculate_amortized_payment


def execute(step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a tool call step.

    For the demo task S2, this calls the calculator tool with the
    loan parameters from the context.

    Args:
        step: The step dictionary containing action and metadata.
        context: Must contain 'principal', 'annual_rate', and 'months'.

    Returns:
        A dictionary containing:
            - tool_call_id: Unique identifier for the tool call
            - payment_value: The calculated payment as a float
            - payment_display: The payment formatted for display

    Raises:
        KeyError: If required context keys are missing.
        ValueError: If the calculation parameters are invalid.
    """
    required_keys = ["principal", "annual_rate", "months"]
    for key in required_keys:
        if key not in context:
            raise KeyError(f"Missing required context key: {key}")

    result = calculate_amortized_payment(
        principal=context["principal"],
        annual_rate=context["annual_rate"],
        months=context["months"],
    )

    return {
        "tool_call_id": result["tool_call_id"],
        "payment_value": result["monthly_payment_value"],
        "payment_display": result["monthly_payment_display"],
    }
