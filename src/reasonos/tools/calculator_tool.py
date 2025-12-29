"""Calculator tool for loan payment calculations."""

from typing import Any

from ..utils.ids import new_event_id


def calculate_amortized_payment(
    principal: float,
    annual_rate: float,
    months: int,
) -> dict[str, Any]:
    """
    Calculate the monthly payment for an amortized loan.

    Uses the standard amortization formula:
    payment = P * i * (1 + i)^n / ((1 + i)^n - 1)

    Where:
        P = principal
        i = monthly interest rate (annual_rate / 12)
        n = number of months

    Args:
        principal: The loan principal amount in dollars.
        annual_rate: The annual interest rate as a decimal (e.g., 0.05 for 5%).
        months: The loan term in months.

    Returns:
        A dictionary with:
            - tool_call_id: Unique identifier for this tool call
            - monthly_payment_value: The calculated payment as a float
            - monthly_payment_display: The payment formatted for display
    """
    if principal <= 0:
        raise ValueError("Principal must be positive")
    if annual_rate < 0:
        raise ValueError("Annual rate cannot be negative")
    if months <= 0:
        raise ValueError("Months must be positive")

    monthly_rate = annual_rate / 12

    if monthly_rate == 0:
        # Handle zero interest rate case
        payment = principal / months
    else:
        # Standard amortization formula
        factor = (1 + monthly_rate) ** months
        payment = principal * monthly_rate * factor / (factor - 1)

    payment_rounded = round(payment, 2)

    return {
        "tool_call_id": new_event_id(),
        "monthly_payment_value": payment_rounded,
        "monthly_payment_display": f"${payment_rounded:.2f}",
    }
