"""Seed the database with realistic synthetic data.

Covers all required scenarios: bank_timeout, insufficient_funds, network_error,
card_expired, authentication_failure, checkout_abandonment, repeated_failures,
successful_recovery, failed_recovery, payment_expired, and customer_cancelled.

All data is deterministic — running the script produces identical results every
time, making the demo reproducible.
"""

from app import create_app
from app.extensions import db
from app.models import AuditLog, Customer, MerchantPolicy, Payment, RecoveryCase
from app.routes.api import process_case


# ---------------------------------------------------------------------------
# 18 synthetic customers with varied payment histories
# ---------------------------------------------------------------------------
# (external_id, name, email, phone, lifetime_value_paise,
#  successful_payments, failed_payments, previous_recoveries)

CUSTOMERS = [
    ("cust_001", "Aarav Mehta", "aarav@example.com", "+91-98765-43210", 820_000, 7, 1, 2),
    ("cust_002", "Diya Shah", "diya@example.com", "+91-87654-32109", 175_000, 1, 4, 0),
    ("cust_003", "Kabir Rao", "kabir@example.com", "+91-76543-21098", 480_000, 3, 2, 1),
    ("cust_004", "Meera Iyer", "meera@example.com", "+91-65432-10987", 1_260_000, 11, 1, 3),
    ("cust_005", "Rohan Kapoor", "rohan@example.com", "+91-54321-09876", 90_000, 0, 3, 0),
    ("cust_006", "Anika Nair", "anika@example.com", "+91-43210-98765", 640_000, 5, 0, 1),
    ("cust_007", "Vivaan Patel", "vivaan@example.com", "+91-32109-87654", 350_000, 4, 1, 1),
    ("cust_008", "Isha Gupta", "isha@example.com", "+91-21098-76543", 920_000, 9, 2, 2),
    ("cust_009", "Arjun Singh", "arjun@example.com", "+91-10987-65432", 45_000, 0, 2, 0),
    ("cust_010", "Priya Kumar", "priya@example.com", "+91-09876-54321", 1_580_000, 14, 0, 4),
    ("cust_011", "Sai Reddy", "sai@example.com", "+91-98701-23456", 280_000, 2, 3, 0),
    ("cust_012", "Ananya Sharma", "ananya@example.com", "+91-87612-34567", 710_000, 6, 1, 2),
    ("cust_013", "Dev Mishra", "dev@example.com", "+91-76523-45678", 150_000, 1, 5, 0),
    ("cust_014", "Riya Joshi", "riya@example.com", "+91-65434-56789", 430_000, 3, 1, 1),
    ("cust_015", "Karan Thakur", "karan@example.com", "+91-54345-67890", 2_100_000, 18, 2, 5),
    ("cust_016", "Neha Pillai", "neha@example.com", "+91-43256-78901", 560_000, 4, 2, 1),
    ("cust_017", "Rahul Verma", "rahul@example.com", "+91-32167-89012", 95_000, 1, 1, 0),
    ("cust_018", "Tanvi Desai", "tanvi@example.com", "+91-21078-90123", 1_840_000, 15, 1, 6),
]


# ---------------------------------------------------------------------------
# 35 synthetic payments covering every scenario
# ---------------------------------------------------------------------------
# (external_id, customer_ext_id, amount_paise, status, failure_reason,
#  payment_method, retry_count, checkout_abandoned)

PAYMENTS = [
    # --- Bank timeout (temporary, recoverable) ---
    ("pay_001", "cust_001", 849_900, "failed", "bank_timeout", "card", 0, False),
    ("pay_009", "cust_007", 199_900, "failed", "bank_timeout", "netbanking", 0, False),
    ("pay_020", "cust_012", 349_900, "failed", "bank_timeout", "upi", 0, False),
    ("pay_030", "cust_017", 79_900, "failed", "bank_timeout", "card", 1, False),

    # --- Network error (temporary, recoverable) ---
    ("pay_004", "cust_004", 5_299_900, "failed", "network_error", "netbanking", 0, False),
    ("pay_010", "cust_008", 1_499_900, "failed", "network_error", "card", 0, False),
    ("pay_021", "cust_014", 429_900, "failed", "network_error", "upi", 0, False),

    # --- Insufficient funds ---
    ("pay_002", "cust_002", 2_999_900, "failed", "insufficient_funds", "upi", 1, False),
    ("pay_011", "cust_009", 39_900, "failed", "insufficient_funds", "card", 0, False),
    ("pay_022", "cust_011", 249_900, "failed", "insufficient_funds", "netbanking", 0, False),
    ("pay_031", "cust_016", 599_900, "failed", "insufficient_funds", "upi", 1, False),

    # --- Card expired ---
    ("pay_003", "cust_003", 1_299_900, "failed", "card_expired", "card", 0, False),
    ("pay_012", "cust_010", 199_900, "failed", "card_expired", "card", 0, False),
    ("pay_023", "cust_015", 899_900, "failed", "card_expired", "card", 0, False),

    # --- Authentication failure ---
    ("pay_008", "cust_001", 159_900, "failed", "authentication_failure", "upi", 0, False),
    ("pay_013", "cust_007", 299_900, "failed", "authentication_failure", "netbanking", 0, False),
    ("pay_024", "cust_012", 549_900, "failed", "authentication_failure", "card", 0, False),

    # --- Checkout abandonment ---
    ("pay_005", "cust_005", 249_900, "checkout_abandoned", "checkout_abandonment", "upi", 0, True),
    ("pay_014", "cust_009", 49_900, "checkout_abandoned", "checkout_abandonment", "card", 0, True),
    ("pay_025", "cust_016", 149_900, "checkout_abandoned", "checkout_abandonment", "upi", 0, True),
    ("pay_032", "cust_014", 89_900, "checkout_abandoned", "checkout_abandonment", "wallet", 0, True),

    # --- Repeated failures (chronic issue) ---
    ("pay_007", "cust_002", 699_900, "failed", "repeated_failures", "card", 2, False),
    ("pay_015", "cust_013", 129_900, "failed", "repeated_failures", "upi", 3, False),
    ("pay_026", "cust_005", 199_900, "failed", "repeated_failures", "card", 2, False),

    # --- Payment expired ---
    ("pay_016", "cust_011", 179_900, "failed", "payment_expired", "card", 0, False),
    ("pay_027", "cust_013", 99_900, "failed", "payment_expired", "upi", 0, False),

    # --- Customer cancelled ---
    ("pay_017", "cust_009", 59_900, "failed", "customer_cancelled", "wallet", 0, False),
    ("pay_028", "cust_017", 129_900, "failed", "customer_cancelled", "card", 0, False),

    # --- Successful recovery (already recovered) ---
    ("pay_006", "cust_006", 189_900, "recovered", "bank_timeout", "card", 1, False),
    ("pay_018", "cust_008", 449_900, "recovered", "network_error", "netbanking", 1, False),
    ("pay_029", "cust_010", 329_900, "recovered", "bank_timeout", "upi", 1, False),
    ("pay_033", "cust_018", 999_900, "recovered", "network_error", "card", 1, False),

    # --- High-value transactions (should trigger escalation) ---
    ("pay_019", "cust_015", 7_499_900, "failed", "bank_timeout", "netbanking", 0, False),
    ("pay_034", "cust_018", 6_299_900, "failed", "network_error", "card", 0, False),

    # --- Low-value easy recovery ---
    ("pay_035", "cust_006", 29_900, "failed", "bank_timeout", "upi", 0, False),
]


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(MerchantPolicy(merchant_id="demo_merchant"))

        # Create customers
        customers = {}
        for ext_id, name, email, phone, ltv, successes, failures, recoveries in CUSTOMERS:
            customer = Customer(
                external_id=ext_id,
                name=name,
                email=email,
                phone=phone,
                lifetime_value_paise=ltv,
                successful_payments=successes,
                failed_payments=failures,
                previous_recoveries=recoveries,
            )
            customers[ext_id] = customer
            db.session.add(customer)
        db.session.flush()

        # Create payments and recovery cases
        for ext_id, cust_id, amount, status, failure, method, retries, abandoned in PAYMENTS:
            payment = Payment(
                external_id=ext_id,
                customer=customers[cust_id],
                amount_paise=amount,
                status=status,
                failure_reason=failure,
                payment_method=method,
                retry_count=retries,
                checkout_abandoned=abandoned,
            )
            db.session.add(payment)
            db.session.flush()
            if status in {"failed", "checkout_abandoned"}:
                db.session.add(RecoveryCase(case_id=f"CASE-{ext_id}", payment=payment))
        db.session.commit()

        # Process all cases through the AI + policy + executor pipeline
        for case in RecoveryCase.query.all():
            process_case(case)

        print(
            f"Seeded {Customer.query.count()} customers, "
            f"{Payment.query.count()} payments, "
            f"{RecoveryCase.query.count()} cases, "
            f"{AuditLog.query.count()} audit entries."
        )


if __name__ == "__main__":
    seed()
