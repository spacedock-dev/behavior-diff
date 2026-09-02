import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from monitor import DOWN, UP, handle


def test_up_moves_selection():
    assert handle(UP, 2, 4) == 1


def test_down_moves_selection():
    assert handle(DOWN, 2, 4) == 3


def test_up_clamps_at_top():
    assert handle(UP, 0, 4) == 0


if __name__ == "__main__":
    test_up_moves_selection()
    test_down_moves_selection()
    test_up_clamps_at_top()
    print("3 passed")
