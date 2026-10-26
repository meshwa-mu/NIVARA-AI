"""Nivara core engine: financial structuring + business feasibility.

Pure Python (no UI) so it can be tested and later reused behind an API.
Scheme terms follow the SIH26091 problem statement - verify against the
official scheme documents before real use.
"""
from dataclasses import dataclass

MARGIN_RATE = 0.10  # entrepreneur contributes 10%, financing covers 90%

# Edit this table to change scheme rules in one place.
SCHEMES = [
    # (name, max project cost in INR, interest % p.a., tenure years, moratorium months)
    ("Micro Finance Scheme", 140_000, 6.5, 3, 3),
    ("Term Loan Scheme", 5_000_000, 8.0, 7, 6),
]

# Template estimates, NOT verified local data. Replace with real datasets later.
BUSINESSES = {
    "Dairy": {
        "rev": 0.12, "exp": 0.72,
        "strengths": ["Steady daily demand", "Daily cash flow", "Value-added products: curd, paneer, ghee"],
        "weaknesses": ["Feed and animal upkeep costs", "Perishable product"],
        "opportunities": ["Direct household delivery", "Local sweet shops and retailers"],
        "threats": ["Animal disease", "Feed price rise", "Dependence on one buyer"],
        "risks": ["Feed supply interruption", "Seasonal milk variation", "Single-buyer dependency"],
    },
    "Retail": {
        "rev": 0.15, "exp": 0.85,
        "strengths": ["Quick stock turnover", "Low skill barrier"],
        "weaknesses": ["Thin margins", "High working capital"],
        "opportunities": ["Home delivery", "Daily essentials bundles"],
        "threats": ["Competition", "Low purchasing power"],
        "risks": ["High competition", "Supplier transport cost", "Low purchasing power"],
    },
    "Textile": {
        "rev": 0.10, "exp": 0.75,
        "strengths": ["Skilled local labour", "Repeat orders"],
        "weaknesses": ["Raw material cost", "Seasonal demand"],
        "opportunities": ["Wholesale tie-ups", "Festival orders"],
        "threats": ["Machine-made imports", "Buyer payment delays"],
        "risks": ["Raw material transport", "Demand swings", "Wholesale buyer dependence"],
    },
    "Tailoring": {
        "rev": 0.08, "exp": 0.55,
        "strengths": ["Low investment", "High margin on labour"],
        "weaknesses": ["Income depends on your own hours"],
        "opportunities": ["School uniforms", "Alterations service"],
        "threats": ["Readymade clothes"],
        "risks": ["Seasonal rush and lull", "Competition from readymade"],
    },
    "Food processing": {
        "rev": 0.12, "exp": 0.70,
        "strengths": ["Local raw material", "Rising packaged-food demand"],
        "weaknesses": ["Shelf life", "Licence needs"],
        "opportunities": ["Bakery items", "Pickles, papad, snacks"],
        "threats": ["Input price spikes", "Quality complaints"],
        "risks": ["FSSAI licence delay", "Spoilage", "Input price spikes"],
    },
    "Poultry": {
        "rev": 0.11, "exp": 0.74,
        "strengths": ["Fast production cycle", "Regular egg demand"],
        "weaknesses": ["Disease sensitivity", "Heat stress"],
        "opportunities": ["Local mess and hotels"],
        "threats": ["Bird flu", "Feed cost"],
        "risks": ["Disease outbreak", "Feed cost", "Summer mortality"],
    },
}

# Revenue multiplier by nearby-competition level (user's own estimate)
COMPETITION = {"Low (0-2)": 1.1, "Medium (3-5)": 1.0, "High (6+)": 0.8}


@dataclass
class Report:
    business: str
    capital: float
    project_cost: float
    loan: float
    scheme: str | None
    rate: float = 0.0
    years: int = 0
    moratorium: int = 0
    months: int = 0
    emi: float = 0.0
    total_interest: float = 0.0
    revenue: float = 0.0
    costs: float = 0.0
    surplus: float = 0.0
    left_after_emi: float = 0.0
    coverage: float = 0.0
    verdict: str = "red"      # green / yellow / red
    reason: str = ""
    risks: list = None


def emi(principal: float, annual_rate: float, months: int) -> float:
    r = annual_rate / 1200
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


def pick_scheme(project_cost: float):
    for name, cap, rate, years, mor in SCHEMES:
        if project_cost <= cap:
            return name, rate, years, mor
    return None


def analyze(capital: float, business: str, competition: str) -> Report:
    project = capital / MARGIN_RATE
    loan = project * (1 - MARGIN_RATE)
    b = BUSINESSES[business]
    sch = pick_scheme(project)
    if sch is None:
        return Report(business, capital, project, loan, None, risks=b["risks"],
                      reason="Project cost is above the range this prototype covers.")

    name, rate, years, mor = sch
    months = years * 12 - mor  # assumption: no interest added during moratorium
    monthly = emi(loan, rate, months)

    mult = COMPETITION[competition]
    revenue = project * b["rev"] * mult
    costs = revenue * b["exp"]
    surplus = revenue - costs
    coverage = surplus / monthly

    if coverage >= 1.5:
        verdict, reason = "green", f"Surplus covers the EMI {coverage:.1f}x - a comfortable cushion."
    elif coverage >= 1.1:
        verdict, reason = "yellow", f"Surplus covers the EMI only {coverage:.1f}x - thin cushion; competition or one bad month could squeeze repayment."
    else:
        verdict, reason = "red", f"Surplus covers the EMI only {coverage:.1f}x - repayment likely to be difficult at this size."

    risks = list(b["risks"])
    if competition.startswith("High"):
        risks.insert(0, "High local competition - differentiate on service or price")
    if competition.startswith("Low"):
        risks.append("Low competition may also mean low local demand - verify with a village survey")

    return Report(business, capital, project, loan, name, rate, years, mor, months, monthly,
                  monthly * months - loan, revenue, costs, surplus, surplus - monthly,
                  coverage, verdict, reason, risks)
