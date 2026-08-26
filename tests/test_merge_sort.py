import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from merge_sort import merge_sort


def test_empty():
    assert merge_sort([]) == []


def test_single():
    assert merge_sort([42]) == [42]


def test_sorted():
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]


def test_reverse():
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]


def test_duplicates():
    assert merge_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]


def test_negative():
    assert merge_sort([-3, 0, 3, -1, 1]) == [-3, -1, 0, 1, 3]
