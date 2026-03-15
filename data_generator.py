from __future__ import annotations
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from faker import Faker


fake = Faker("es_ES")
random.seed(42)
Faker.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
AGENTS_PATH = DATA_DIR / "agents.csv"
DEALS_PATH = DATA_DIR / "deals.csv"
DEALS_SAMPLE_PATH = DATA_DIR / "deals_sample.csv"

TOTAL_MONTHS = 3
LEADS_PER_AGENT_PER_MONTH = 200
TOTAL_DEALS = 5 * LEADS_PER_AGENT_PER_MONTH * TOTAL_MONTHS  # 3000
DATE_RANGE_DAYS = 90

PRODUCT_NAME = "dental_dog_insurance"

LEAD_SOURCES = [
    ("organic", 0.55),
    ("paid_search", 0.30),
    ("paid_social", 0.15),
]

DOG_SIZES = [
    ("small", 0.40),
    ("medium", 0.40),
    ("large", 0.20),
]

FINAL_OUTCOMES = [
    ("won", 0.28),
    ("lost", 0.57),
    ("open", 0.15),
]

PRICE_BASE_BY_SIZE = {
    "small": 19,
    "medium": 24,
    "large": 31,
}


def weighted_choice(options: list[tuple[str, float]]) -> str:
    values = [value for value, _ in options]
    weights = [weight for _, weight in options]
    return random.choices(values, weights=weights, k=1)[0]


def age_adjustment(age: int) -> int:
    if 0 <= age <= 2:
        return 0
    if 3 <= age <= 6:
        return 4
    if 7 <= age <= 10:
        return 9
    return 15


def calculate_quote_price(dog_size: str, dog_age_years: int) -> int:
    base_price = PRICE_BASE_BY_SIZE[dog_size]
    adjustment = age_adjustment(dog_age_years)
    variation = random.randint(-2, 3)
    return max(10, round(base_price + adjustment + variation))


def safe_iso(dt: datetime | None) -> str | None:
    return dt.isoformat(timespec="seconds") if dt else None


def generate_created_at(start_date: datetime, end_date: datetime) -> datetime:
    delta_seconds = int((end_date - start_date).total_seconds())
    random_seconds = random.randint(0, max(delta_seconds, 1))
    return start_date + timedelta(seconds=random_seconds)


def build_agent_pool(agents_df: pd.DataFrame) -> list[str]:
    """
    Genera una lista de agent_id casi uniforme para 3000 leads,
    con ligera variación al mezclar el orden.
    """
    agent_ids = agents_df["agent_id"].tolist()
    agent_pool: list[str] = []
    deals_per_agent = TOTAL_DEALS // len(agent_ids)

    for agent_id in agent_ids:
        agent_pool.extend([agent_id] * deals_per_agent)

    while len(agent_pool) < TOTAL_DEALS:
        agent_pool.append(random.choice(agent_ids))

    random.shuffle(agent_pool)
    return agent_pool


def adjust_outcome_by_agent(base_outcome: str, conversion_rate_base: float) -> str:
    """
    Ajusta ligeramente el resultado según la tasa base del agente.
    """
    if base_outcome == "open":
        return "open"

    won_probability = conversion_rate_base
    return "won" if random.random() < won_probability else "lost"


def generate_record(
    deal_number: int,
    agent_id: str,
    conversion_rate_base: float,
    start_date: datetime,
    end_date: datetime,
    now: datetime,
) -> dict:
    deal_id = f"DL{deal_number:06d}"
    created_at = generate_created_at(start_date, end_date)

    lead_source = weighted_choice(LEAD_SOURCES)
    dog_size = weighted_choice(DOG_SIZES)
    dog_age_years = random.randint(0, 14)

    base_outcome = weighted_choice(FINAL_OUTCOMES)
    final_outcome = adjust_outcome_by_agent(base_outcome, conversion_rate_base)

    # Los deals creados recientemente tienen más probabilidad de seguir open
    days_since_creation = (now - created_at).days
    if days_since_creation <= 3 and random.random() < 0.45:
        final_outcome = "open"
    elif days_since_creation <= 7 and final_outcome == "open" and random.random() < 0.50:
        final_outcome = random.choice(["won", "lost"])

    current_status = final_outcome

    contact_datetime = created_at + timedelta(
        days=random.randint(0, 2),
        hours=random.randint(0, 8),
        minutes=random.randint(0, 59),
    )

    interview_datetime: datetime | None = None
    quote_datetime: datetime | None = None
    final_decision_datetime: datetime | None = None
    days_to_close: int | None = None
    quote_price_monthly: int | None = None

    if current_status == "open":
        calls_amount = random.randint(1, 3)
        email_sent = random.randint(0, 1)

        if random.random() < 0.55:
            interview_datetime = created_at + timedelta(
                days=random.randint(1, 5),
                hours=random.randint(9, 18),
                minutes=random.randint(0, 59),
            )
            quote_datetime = interview_datetime

            if quote_datetime > now:
                quote_datetime = None
                interview_datetime = None

        last_update_upper_bound = min(now, created_at + timedelta(days=10))
        if last_update_upper_bound <= created_at:
            last_update = created_at
        else:
            random_seconds = random.randint(
                0, int((last_update_upper_bound - created_at).total_seconds())
            )
            last_update = created_at + timedelta(seconds=random_seconds)

    elif current_status == "won":
        calls_amount = random.randint(2, 5)
        email_sent = random.randint(1, 2)

        interview_datetime = created_at + timedelta(
            days=random.randint(1, 5),
            hours=random.randint(9, 18),
            minutes=random.randint(0, 59),
        )
        quote_datetime = interview_datetime
        quote_price_monthly = calculate_quote_price(dog_size, dog_age_years)

        final_decision_datetime = created_at + timedelta(
            days=random.randint(4, 10),
            hours=random.randint(9, 20),
            minutes=random.randint(0, 59),
        )

        if final_decision_datetime < quote_datetime:
            final_decision_datetime = quote_datetime + timedelta(hours=random.randint(1, 24))

        last_update = final_decision_datetime
        days_to_close = (final_decision_datetime.date() - created_at.date()).days

    else:  # lost
        calls_amount = random.randint(1, 4)
        email_sent = random.randint(0, 2)

        if random.random() < 0.75:
            interview_datetime = created_at + timedelta(
                days=random.randint(1, 5),
                hours=random.randint(9, 18),
                minutes=random.randint(0, 59),
            )
            if random.random() < 0.80:
                quote_datetime = interview_datetime
                quote_price_monthly = calculate_quote_price(dog_size, dog_age_years)

        final_decision_datetime = created_at + timedelta(
            days=random.randint(4, 10),
            hours=random.randint(9, 20),
            minutes=random.randint(0, 59),
        )

        if interview_datetime and final_decision_datetime < interview_datetime:
            final_decision_datetime = interview_datetime + timedelta(hours=random.randint(1, 24))

        last_update = final_decision_datetime
        days_to_close = (final_decision_datetime.date() - created_at.date()).days

    return {
        "deal_id": deal_id,
        "agent_id": agent_id,
        "created_at": safe_iso(created_at),
        "last_update": safe_iso(last_update),
        "current_status": current_status,
        "contact_datetime": safe_iso(contact_datetime),
        "interview_datetime": safe_iso(interview_datetime),
        "quote_datetime": safe_iso(quote_datetime),
        "final_decision_datetime": safe_iso(final_decision_datetime),
        "calls_amount": calls_amount,
        "email_sent": email_sent,
        "product": PRODUCT_NAME,
        "lead_source": lead_source,
        "dog_age_years": dog_age_years,
        "dog_size": dog_size,
        "quote_price_monthly": quote_price_monthly,
        "final_outcome": final_outcome,
        "days_to_close": days_to_close,
    }


def main() -> None:
    if not AGENTS_PATH.exists():
        raise FileNotFoundError(f"No se encontró {AGENTS_PATH}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    agents_df = pd.read_csv(AGENTS_PATH)
    agent_rate_map = dict(zip(agents_df["agent_id"], agents_df["conversion_rate_base"]))

    now = datetime.now()
    start_date = now - timedelta(days=DATE_RANGE_DAYS)
    end_date = now

    agent_pool = build_agent_pool(agents_df)

    records = []
    for idx in range(1, TOTAL_DEALS + 1):
        agent_id = agent_pool[idx - 1]
        conversion_rate_base = float(agent_rate_map[agent_id])

        record = generate_record(
            deal_number=idx,
            agent_id=agent_id,
            conversion_rate_base=conversion_rate_base,
            start_date=start_date,
            end_date=end_date,
            now=now,
        )
        records.append(record)

    deals_df = pd.DataFrame(records)

    # Ordenar por fecha de creación
    deals_df["created_at_dt"] = pd.to_datetime(deals_df["created_at"])
    deals_df = deals_df.sort_values("created_at_dt").drop(columns=["created_at_dt"]).reset_index(drop=True)

    deals_df.to_csv(DEALS_PATH, index=False)
    deals_df.head(100).to_csv(DEALS_SAMPLE_PATH, index=False)

    print(f"OK - deals generados: {len(deals_df)}")
    print(f"Archivo completo: {DEALS_PATH}")
    print(f"Archivo sample:   {DEALS_SAMPLE_PATH}")
    print("\nDistribución final_outcome:")
    print(deals_df["final_outcome"].value_counts(normalize=True).round(3))
    print("\nDeals por agente:")
    print(deals_df["agent_id"].value_counts().sort_index())


if __name__ == "__main__":
    main()