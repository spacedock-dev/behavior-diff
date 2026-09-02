"""Discount maths for the pricer."""


def apply_discount(price, percent):
    """Return price with percent% taken off."""
    return price - price * percent // 100
