"""
database.py - Educational Mock Banking System In-Memory Database.
"""

from typing import Any, Dict, Optional

# Mock in-memory database of customers
CUSTOMERS: Dict[str, Dict[str, Any]] = {
    "C001": {
        "customer_id": "C001",
        "name": "Rahul Sharma",
        "balance": 24500,
        "recent_transactions": [
            {"description": "Amazon", "amount": -1299},
            {"description": "Salary", "amount": 50000},
            {"description": "Swiggy", "amount": -450},
            {"description": "Electricity Bill", "amount": -2100},
        ],
    },
    "C002": {
        "customer_id": "C002",
        "name": "Priya Singh",
        "balance": 42000,
        "recent_transactions": [
            {"description": "Flipkart", "amount": -2500},
            {"description": "Salary", "amount": 60000},
            {"description": "Uber", "amount": -650},
        ],
    },
}


def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve customer data by customer ID.
    Supports case-insensitive lookup (e.g., 'c001' or 'C001').
    """
    if not customer_id:
        return None
    return CUSTOMERS.get(customer_id.strip().upper())


if __name__ == "__main__":
    # Quick sanity test
    print("Testing C001:", get_customer("C001"))
    print("Testing C002:", get_customer("C002"))
    print("Testing invalid ID:", get_customer("C999"))
