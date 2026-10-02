"""
banking_tools.py - Deterministic banking operations and business rules.
"""

from typing import Any, Dict, List, Optional
from database import get_customer
from guardrails import authorize_customer_access

ALLOWED_BENEFICIARIES: List[str] = ["Rahul", "Priya"]
MAX_TRANSFER_LIMIT: float = 10000.0


class ValidationResult(dict):
    """
    Validation result object that supports:
    - Dict access: res["valid"], res["message"]
    - Property access: res.valid, res.message
    - Boolean evaluation: bool(res) is True only when valid
    - Tuple unpacking: is_valid, msg = res
    """

    def __init__(self, valid: bool, message: str):
        super().__init__(valid=valid, success=valid, message=message)
        self.valid = valid
        self.is_valid = valid
        self.message = message

    def __bool__(self) -> bool:
        return self.valid

    def __iter__(self):
        return iter((self.valid, self.message))


class TransferResult(dict):
    """
    Transfer execution result object that evaluates to True on success.
    """

    def __init__(self, success: bool, message: str, **kwargs):
        super().__init__(success=success, message=message, **kwargs)
        self.success = success
        self.message = message

    def __bool__(self) -> bool:
        return self.success


def get_balance(
    customer_id: str, authenticated_customer_id: Optional[str] = None
) -> Optional[float]:
    """
    Return the customer's current balance after authorization check.
    Returns None if customer does not exist or access is unauthorized.
    """
    if authenticated_customer_id is not None:
        auth = authorize_customer_access(authenticated_customer_id, customer_id)
        if not auth.get("allowed", False):
            return None

    customer = get_customer(customer_id)
    if not customer:
        return None
    return customer["balance"]


def get_transactions(
    customer_id: str, authenticated_customer_id: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Return the customer's recent transactions after authorization check.
    Returns None if customer does not exist or access is unauthorized.
    """
    if authenticated_customer_id is not None:
        auth = authorize_customer_access(authenticated_customer_id, customer_id)
        if not auth.get("allowed", False):
            return None

    customer = get_customer(customer_id)
    if not customer:
        return None
    return customer["recent_transactions"]


def validate_transfer(
    customer_id: str,
    amount: float,
    receiver: str,
    authenticated_customer_id: Optional[str] = None,
) -> ValidationResult:
    """
    Validate transfer parameters against business rules:
    - Authorization check (authenticated_customer_id matches customer_id)
    - Customer must exist
    - Amount must be positive
    - Amount must not exceed 10000 (MAX_TRANSFER_LIMIT)
    - Customer must have sufficient balance
    - Receiver must be an allowed mock beneficiary
    - Sender cannot transfer funds to themselves
    """
    # 0. Authorization check
    if authenticated_customer_id is not None:
        auth = authorize_customer_access(authenticated_customer_id, customer_id)
        if not auth.get("allowed", False):
            return ValidationResult(False, auth.get("reason", "Authorization Denied."))
    # 1. Customer exists
    customer = get_customer(customer_id)
    if not customer:
        return ValidationResult(
            False, f"Validation failed: Customer ID '{customer_id}' does not exist."
        )

    # 2. Amount is a positive number
    try:
        amt = float(amount)
    except (ValueError, TypeError):
        return ValidationResult(
            False, "Validation failed: Amount must be a valid numeric value."
        )

    if amt <= 0:
        return ValidationResult(
            False, "Validation failed: Amount must be greater than zero."
        )

    # 3. Amount does not exceed 10000
    if amt > MAX_TRANSFER_LIMIT:
        return ValidationResult(
            False,
            f"Validation failed: Transfer amount (₹{amt:g}) exceeds the maximum limit of ₹{MAX_TRANSFER_LIMIT:g}.",
        )

    # 4. Customer has sufficient balance
    current_balance = customer["balance"]
    if current_balance < amt:
        return ValidationResult(
            False,
            f"Validation failed: Insufficient balance. Available: ₹{current_balance:g}, Required: ₹{amt:g}.",
        )

    # 5. Receiver is an allowed mock beneficiary
    if not receiver or not isinstance(receiver, str):
        return ValidationResult(
            False, "Validation failed: Receiver name must be provided."
        )

    matched_beneficiary = next(
        (b for b in ALLOWED_BENEFICIARIES if b.lower() == receiver.strip().lower()),
        None,
    )
    if not matched_beneficiary:
        allowed_names = ", ".join(ALLOWED_BENEFICIARIES)
        return ValidationResult(
            False,
            f"Validation failed: '{receiver}' is not an allowed beneficiary. Allowed beneficiaries: {allowed_names}.",
        )

    # 6. Cannot transfer to oneself
    sender_first_name = customer["name"].split()[0].lower()
    if matched_beneficiary.lower() == sender_first_name:
        return ValidationResult(
            False, "Validation failed: Cannot transfer funds to yourself."
        )

    return ValidationResult(
        True,
        f"Validation successful: Ready to transfer ₹{amt:g} to {matched_beneficiary}.",
    )


def execute_transfer(
    customer_id: str,
    amount: float,
    receiver: str,
    authenticated_customer_id: Optional[str] = None,
) -> TransferResult:
    """
    Execute transfer after deterministic validation:
    - Authorization check (authenticated_customer_id matches customer_id)
    - Only execute after validate_transfer succeeds
    - Update sender's balance and transaction history
    - Credit receiver if beneficiary exists in mock database
    """
    # 0. Authorization check
    if authenticated_customer_id is not None:
        auth = authorize_customer_access(authenticated_customer_id, customer_id)
        if not auth.get("allowed", False):
            return TransferResult(
                False,
                auth.get("reason", "Authorization Denied."),
                customer_id=customer_id,
                amount=amount,
                receiver=receiver,
            )

    # Deterministic business validation
    validation = validate_transfer(
        customer_id=customer_id,
        amount=amount,
        receiver=receiver,
        authenticated_customer_id=authenticated_customer_id,
    )
    if not validation:
        return TransferResult(
            False,
            validation.message,
            customer_id=customer_id,
            amount=amount,
            receiver=receiver,
        )

    amt = float(amount)
    customer = get_customer(customer_id)
    matched_beneficiary = next(
        b for b in ALLOWED_BENEFICIARIES if b.lower() == receiver.strip().lower()
    )

    # Update sender balance and history
    customer["balance"] -= amt
    sender_entry = {
        "description": f"Transfer to {matched_beneficiary}",
        "amount": -amt,
    }
    customer["recent_transactions"].append(sender_entry)

    # Credit receiver if they exist in the database (e.g., C001 is Rahul, C002 is Priya)
    beneficiary_first = matched_beneficiary.lower()
    for cid in ["C001", "C002"]:
        beneficiary_customer = get_customer(cid)
        if (
            beneficiary_customer
            and beneficiary_customer["name"].split()[0].lower() == beneficiary_first
            and beneficiary_customer["customer_id"] != customer["customer_id"]
        ):
            beneficiary_customer["balance"] += amt
            beneficiary_customer["recent_transactions"].append(
                {
                    "description": f"Transfer from {customer['name'].split()[0]}",
                    "amount": amt,
                }
            )

    return TransferResult(
        True,
        f"Successfully transferred ₹{amt:g} to {matched_beneficiary}.",
        customer_id=customer["customer_id"],
        receiver=matched_beneficiary,
        amount=amt,
        new_balance=customer["balance"],
        transaction=sender_entry,
    )


if __name__ == "__main__":
    print("--- Initial Balances ---")
    print("C001 Balance:", get_balance("C001"))
    print("C002 Balance:", get_balance("C002"))

    print("\n--- Test Validations ---")
    print("Exceed Limit (15000):", validate_transfer("C001", 15000, "Priya"))
    print("Invalid Receiver (Bob):", validate_transfer("C001", 500, "Bob"))
    print("Self Transfer (Rahul):", validate_transfer("C001", 500, "Rahul"))
    print("Valid Transfer (5000 to Priya):", validate_transfer("C001", 5000, "Priya"))

    print("\n--- Test Execution ---")
    res = execute_transfer("C001", 5000, "Priya")
    print("Execution Result:", res)
    print("C001 New Balance:", get_balance("C001"))
    print("C002 New Balance:", get_balance("C002"))
