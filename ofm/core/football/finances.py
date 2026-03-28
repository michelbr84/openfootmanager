from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    INCOME = "Income"
    EXPENSE = "Expense"


class RevenueType(Enum):
    TICKET_SALES = "Ticket Sales"
    TV_RIGHTS = "TV Rights"
    MERCHANDISE = "Merchandise"
    SPONSORSHIP = "Sponsorship"
    TRANSFER_FEE = "Transfer Fee"
    PRIZE_MONEY = "Prize Money"
    OTHER = "Other"


class ExpenseType(Enum):
    WAGES = "Wages"
    TRANSFER_FEE = "Transfer Fee"
    AGENT_FEE = "Agent Fee"
    STADIUM_MAINTENANCE = "Stadium Maintenance"
    TRAINING_FACILITY = "Training Facility"
    YOUTH_ACADEMY = "Youth Academy"
    BONUS = "Bonus"
    OTHER = "Other"


@dataclass
class Transaction:
    amount: float
    description: str
    date: datetime
    type: TransactionType
    revenue_type: Optional[RevenueType] = None
    expense_type: Optional[ExpenseType] = None

    def serialize(self) -> dict:
        data = {
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat(),
            "type": self.type.value,
        }
        if self.revenue_type is not None:
            data["revenue_type"] = self.revenue_type.value
        if self.expense_type is not None:
            data["expense_type"] = self.expense_type.value
        return data

    @classmethod
    def get_from_dict(cls, data: dict) -> "Transaction":
        revenue_type = None
        expense_type = None
        if "revenue_type" in data:
            revenue_type = RevenueType(data["revenue_type"])
        if "expense_type" in data:
            expense_type = ExpenseType(data["expense_type"])
        return cls(
            amount=data["amount"],
            description=data["description"],
            date=datetime.fromisoformat(data["date"]),
            type=TransactionType(data["type"]),
            revenue_type=revenue_type,
            expense_type=expense_type,
        )


@dataclass
class SponsorshipDeal:
    sponsor_name: str
    annual_amount: float
    start_date: datetime
    end_date: datetime
    bonus_clauses: dict = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        now = datetime.now()
        return self.start_date <= now <= self.end_date

    def serialize(self) -> dict:
        return {
            "sponsor_name": self.sponsor_name,
            "annual_amount": self.annual_amount,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "bonus_clauses": self.bonus_clauses,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "SponsorshipDeal":
        return cls(
            sponsor_name=data["sponsor_name"],
            annual_amount=data["annual_amount"],
            start_date=datetime.fromisoformat(data["start_date"]),
            end_date=datetime.fromisoformat(data["end_date"]),
            bonus_clauses=data.get("bonus_clauses", {}),
        )


@dataclass
class SeasonBudget:
    transfer_budget: float
    wage_budget: float
    transfer_spent: float = 0.0
    wage_spent: float = 0.0

    @property
    def transfer_remaining(self) -> float:
        return self.transfer_budget - self.transfer_spent

    @property
    def wage_remaining(self) -> float:
        return self.wage_budget - self.wage_spent

    def can_afford_transfer(self, amount: float) -> bool:
        return amount <= self.transfer_remaining

    def can_afford_wage(self, weekly_wage: float) -> bool:
        annual_wage = weekly_wage * 52
        return annual_wage <= self.wage_remaining

    def spend_transfer(self, amount: float):
        self.transfer_spent += amount

    def spend_wage(self, weekly_wage: float):
        annual_wage = weekly_wage * 52
        self.wage_spent += annual_wage

    def serialize(self) -> dict:
        return {
            "transfer_budget": self.transfer_budget,
            "wage_budget": self.wage_budget,
            "transfer_spent": self.transfer_spent,
            "wage_spent": self.wage_spent,
        }

    @classmethod
    def get_from_dict(cls, data: dict) -> "SeasonBudget":
        return cls(
            transfer_budget=data["transfer_budget"],
            wage_budget=data["wage_budget"],
            transfer_spent=data.get("transfer_spent", 0.0),
            wage_spent=data.get("wage_spent", 0.0),
        )


@dataclass
class FinanceManager:
    balance: float = 0.0
    transactions: list[Transaction] = field(default_factory=list)
    sponsorship_deals: list[SponsorshipDeal] = field(default_factory=list)
    season_budget: Optional[SeasonBudget] = None

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

    def _add_categorized_income(
        self, amount: float, description: str, revenue_type: RevenueType
    ):
        self.balance += amount
        self.transactions.append(
            Transaction(
                amount, description, datetime.now(), TransactionType.INCOME,
                revenue_type=revenue_type,
            )
        )

    def _add_categorized_expense(
        self, amount: float, description: str, expense_type: ExpenseType
    ):
        self.balance -= amount
        self.transactions.append(
            Transaction(
                amount, description, datetime.now(), TransactionType.EXPENSE,
                expense_type=expense_type,
            )
        )

    def add_sponsorship(self, deal: SponsorshipDeal):
        self.sponsorship_deals.append(deal)
        self._add_categorized_income(
            deal.annual_amount,
            f"Sponsorship deal: {deal.sponsor_name}",
            RevenueType.SPONSORSHIP,
        )

    def calculate_matchday_revenue(
        self, attendance: int, ticket_price: float = 25.0
    ) -> float:
        revenue = attendance * ticket_price
        self._add_categorized_income(
            revenue,
            f"Matchday revenue ({attendance} attendance @ {ticket_price})",
            RevenueType.TICKET_SALES,
        )
        return revenue

    def calculate_tv_revenue(
        self,
        league_position: int,
        total_clubs: int,
        base_amount: float = 5_000_000.0,
    ) -> float:
        # Higher position (lower number) = more money
        # Position 1 gets full base, last place gets base / total_clubs
        if total_clubs <= 1:
            share = base_amount
        else:
            share = base_amount * (total_clubs - league_position + 1) / total_clubs
        self._add_categorized_income(
            share,
            f"TV revenue (position {league_position}/{total_clubs})",
            RevenueType.TV_RIGHTS,
        )
        return share

    def pay_weekly_wages(self, squad_wages: float):
        self._add_categorized_expense(
            squad_wages, "Weekly squad wages", ExpenseType.WAGES
        )
        if self.season_budget is not None:
            # Track weekly wage in budget as the weekly portion
            self.season_budget.wage_spent += squad_wages

    def process_transfer_income(self, amount: float, player_name: str):
        self._add_categorized_income(
            amount,
            f"Transfer income: {player_name}",
            RevenueType.TRANSFER_FEE,
        )

    def process_transfer_expense(self, amount: float, player_name: str):
        self._add_categorized_expense(
            amount,
            f"Transfer expense: {player_name}",
            ExpenseType.TRANSFER_FEE,
        )
        if self.season_budget is not None:
            self.season_budget.spend_transfer(amount)

    def get_season_report(self) -> dict:
        income_by_type: dict[str, float] = {}
        expense_by_type: dict[str, float] = {}

        total_income = 0.0
        total_expenses = 0.0

        for t in self.transactions:
            if t.type == TransactionType.INCOME:
                total_income += t.amount
                key = t.revenue_type.value if t.revenue_type else RevenueType.OTHER.value
                income_by_type[key] = income_by_type.get(key, 0.0) + t.amount
            elif t.type == TransactionType.EXPENSE:
                total_expenses += t.amount
                key = t.expense_type.value if t.expense_type else ExpenseType.OTHER.value
                expense_by_type[key] = expense_by_type.get(key, 0.0) + t.amount

        report = {
            "balance": self.balance,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "income_by_type": income_by_type,
            "expense_by_type": expense_by_type,
        }

        if self.season_budget is not None:
            report["budget"] = {
                "transfer_budget": self.season_budget.transfer_budget,
                "transfer_spent": self.season_budget.transfer_spent,
                "transfer_remaining": self.season_budget.transfer_remaining,
                "wage_budget": self.season_budget.wage_budget,
                "wage_spent": self.season_budget.wage_spent,
                "wage_remaining": self.season_budget.wage_remaining,
            }

        return report

    def set_season_budget(self, transfer_budget: float, wage_budget: float):
        self.season_budget = SeasonBudget(
            transfer_budget=transfer_budget, wage_budget=wage_budget
        )

    def serialize(self) -> dict:
        data: dict = {
            "balance": self.balance,
            "transactions": [t.serialize() for t in self.transactions],
            "sponsorship_deals": [d.serialize() for d in self.sponsorship_deals],
        }
        if self.season_budget is not None:
            data["season_budget"] = self.season_budget.serialize()
        return data

    @classmethod
    def get_from_dict(cls, data: dict) -> "FinanceManager":
        transactions = [
            Transaction.get_from_dict(t) for t in data.get("transactions", [])
        ]
        sponsorship_deals = [
            SponsorshipDeal.get_from_dict(d)
            for d in data.get("sponsorship_deals", [])
        ]
        season_budget = None
        if "season_budget" in data:
            season_budget = SeasonBudget.get_from_dict(data["season_budget"])
        return cls(
            balance=data.get("balance", 0.0),
            transactions=transactions,
            sponsorship_deals=sponsorship_deals,
            season_budget=season_budget,
        )
