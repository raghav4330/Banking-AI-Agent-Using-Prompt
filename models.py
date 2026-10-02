"""
models.py - Data schemas and transfer structures for the Banking AI Agent.
"""

from typing import Optional


class PendingTransfer(dict):
    """
    Represents a validated transfer awaiting explicit human/user confirmation.
    Contains:
    - customer_id: str
    - receiver: str
    - amount: float
    - status: "PENDING_CONFIRMATION"

    Supports both dictionary subscript access and attribute access.
    """

    def __init__(
        self,
        customer_id: str,
        receiver: str,
        amount: float,
        status: str = "PENDING_CONFIRMATION",
        message: Optional[str] = None,
    ):
        amt = float(amount)
        msg = message or f"Transfer of ₹{amt:g} to {receiver} is pending confirmation."
        super().__init__(
            customer_id=customer_id,
            receiver=receiver,
            amount=amt,
            status=status,
            message=msg,
        )
        self.customer_id = customer_id
        self.receiver = receiver
        self.amount = amt
        self.status = status
        self.message = msg

    def __repr__(self) -> str:
        return f"PendingTransfer({dict(self)})"

    def __str__(self) -> str:
        return (
            f"Transfer Pending Confirmation:\n"
            f"• Customer ID: {self.customer_id}\n"
            f"• Beneficiary: {self.receiver}\n"
            f"• Amount: ₹{self.amount:,.2f}\n"
            f"• Status: {self.status}\n\n"
            f"Please confirm: Do you want to proceed with this transfer?"
        )
