from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class TransactionType(Enum):
    INCOME = "Income"
    EXPENSE = "Expense"

@dataclass
class Transaction:
    amount: float
    description: str
    date: datetime
    type: TransactionType

@dataclass
class FinanceManager:
    balance: float = 0.0
    transactions: list[Transaction] = field(default_factory=list)

    def add_income(self, amount: float, description: str):
        self.balance += amount
        self.transactions.append(
            Transaction(amount, description, datetime.now(), TransactionType.INCOME)
        )

    def add_expense(self, amount: float, description: str):
        if amount > self.balance:
            # Allow debt? For now, yes, but maybe warn.
            pass
        self.balance -= amount
        self.transactions.append(
            Transaction(amount, description, datetime.now(), TransactionType.EXPENSE)
        )

    def get_summary(self) -> dict:
        return {
            "balance": self.balance,
            "transaction_count": len(self.transactions)
        }
