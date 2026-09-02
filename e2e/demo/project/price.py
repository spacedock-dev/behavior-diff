#!/usr/bin/env python3
"""Print what a customer pays after a discount.

Usage: python3 price.py PRICE PERCENT
"""
import sys

from discount import apply_discount


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip())
        return 1
    price = float(sys.argv[1])
    percent = float(sys.argv[2])
    print(f"{apply_discount(price, percent):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
