import pytest

from wu_diff import DiffElement, DiffType, compare


@pytest.mark.parametrize(
    "old, new, answer",
    [
        ("", "", []),
        ("a", "a", [DiffElement(old_index=0, new_index=0, diff_type=DiffType.COMMON)]),
        ("a", "", [DiffElement(old_index=0, new_index=None, diff_type=DiffType.REMOVED)]),
        ("", "a", [DiffElement(old_index=None, new_index=0, diff_type=DiffType.ADDED)]),
        (
            "a",
            "b",
            [
                DiffElement(new_index=0, old_index=None, diff_type=DiffType.ADDED),
                DiffElement(new_index=None, old_index=0, diff_type=DiffType.REMOVED),
            ],
        ),
        (
            "strength",
            "string",
            [
                DiffElement(old_index=0, new_index=0, diff_type=DiffType.COMMON),
                DiffElement(old_index=1, new_index=1, diff_type=DiffType.COMMON),
                DiffElement(old_index=2, new_index=2, diff_type=DiffType.COMMON),
                DiffElement(old_index=3, new_index=None, diff_type=DiffType.REMOVED),
                DiffElement(old_index=None, new_index=3, diff_type=DiffType.ADDED),
                DiffElement(old_index=4, new_index=4, diff_type=DiffType.COMMON),
                DiffElement(old_index=5, new_index=5, diff_type=DiffType.COMMON),
                DiffElement(old_index=6, new_index=None, diff_type=DiffType.REMOVED),
                DiffElement(old_index=7, new_index=None, diff_type=DiffType.REMOVED),
            ],
        ),
    ],
)
def test_compare(old, new, answer):
    assert compare(old, new) == answer
