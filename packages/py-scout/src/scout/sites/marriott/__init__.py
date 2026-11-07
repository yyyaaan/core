"""marriott.com: behind Akamai Bot Manager, so every request runs inside a real browser tab."""

XPF_PER_EUR = 1000 / 8.38  # fixed peg


def eur(amount: float, currency: str) -> float | None:
    return amount / XPF_PER_EUR if currency == "XPF" else None
