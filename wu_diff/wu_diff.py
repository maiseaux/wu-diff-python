from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, DefaultDict, Generic, List, Optional, Tuple, TypeVar

T = TypeVar("T")


class DiffType(Enum):
    COMMON = auto()
    ADDED = auto()
    REMOVED = auto()


@dataclass
class DiffElement:
    old_index: Optional[int] = None
    new_index: Optional[int] = None
    diff_type: DiffType = DiffType.COMMON


@dataclass
class FurthestPoint:
    furthest_y: int = -1
    prev_y: int = -1
    prev_p: int = 0
    diff_type: DiffType = DiffType.COMMON


class WuDiff(Generic[T]):
    old: List[T]
    new: List[T]
    is_equal: Callable[[T, T], bool]
    prefix: List[T]
    suffix: List[T]
    prefix_size: int
    swapped: bool
    A: List[T]
    M: int
    B: List[T]
    N: int
    delta: int
    fp: DefaultDict[Tuple[int, int], FurthestPoint]
    P: int
    ses: List[DiffElement]

    def __init__(self, old: List[T], new: List[T], is_equal: Callable[[T, T], bool] = lambda a, b: a == b):
        self.old = old
        self.new = new
        self.is_equal = is_equal
        self._get_prefix()
        self._get_suffix()
        self._get_body()
        self._compose_fp()
        self._compose_ses()

    @property
    def edit_distance(self):
        return self.delta + 2 * self.P

    def _get_prefix(self):
        prefix: List[T] = []
        for i in range(min(len(self.old), len(self.new))):
            if self.is_equal(self.old[i], self.new[i]):
                prefix.append(self.old[i])
            else:
                break
        self.prefix = prefix
        self.prefix_size = len(prefix)

    def _get_suffix(self):
        suffix: List[T] = []
        for i in range(min(len(self.old), len(self.new)) - self.prefix_size):
            if self.is_equal(self.old[-(i + 1)], self.new[-(i + 1)]):
                suffix.append(self.old[i])
            else:
                break
        self.suffix = suffix

    def _get_body(self):
        old_body = self.old[self.prefix_size : len(self.old) - len(self.suffix)]
        new_body = self.new[self.prefix_size : len(self.new) - len(self.suffix)]

        # NOTE: B is longer than A (M < N)
        self.swapped = len(self.new) < len(self.old)
        self.A, self.B = (new_body, old_body) if self.swapped else (old_body, new_body)
        self.M, self.N = len(self.A), len(self.B)
        self.delta = self.N - self.M

    @staticmethod
    def _display_block(old: str, new: str):
        if old and new:
            print(" " + old)
        elif old:
            print("-" + old)
        else:
            print("+" + new)

    def display_diff(self, old: Optional[List[str]] = None, new: Optional[List[str]] = None, sep: str = ""):
        if not old:
            old = self.old
        if not new:
            new = self.new

        old_cur, new_cur = "", ""
        for diff in self.ses:
            if diff.diff_type == DiffType.COMMON:
                old_cur += old[diff.old_index] + sep
                new_cur += new[diff.new_index] + sep
            elif len(old_cur) > 0 or len(new_cur) > 0:
                self._display_block(old_cur, new_cur)
                old_cur, new_cur = "", ""

            if diff.diff_type == DiffType.ADDED:
                self._display_block("", new[diff.new_index])

            if diff.diff_type == DiffType.REMOVED:
                self._display_block(old[diff.old_index], "")
        if len(old_cur) > 0 or len(new_cur) > 0:
            self._display_block(old_cur, new_cur)

    def _snake(self, k: int, y: int) -> int:
        while y - k < self.M and y < self.N and self.is_equal(self.A[y - k], self.B[y]):
            y += 1
        return y

    def _compose_fp(self):
        self.fp = defaultdict(FurthestPoint)
        if not self.M:
            self.P = 0
            return

        p = 0

        def set_fp(k: int, p: int, added: int, removed: int, place: str):
            if added > removed:
                prev_p = p - 1 if place == "upper" else p
                self.fp[(k, p)] = FurthestPoint(
                    furthest_y=self._snake(k, added),
                    prev_y=added,
                    prev_p=prev_p,
                    diff_type=DiffType.ADDED,
                )
            else:
                prev_p = p - 1 if place == "lower" else p
                self.fp[(k, p)] = FurthestPoint(
                    furthest_y=self._snake(k, removed),
                    prev_y=removed,
                    prev_p=prev_p,
                    diff_type=DiffType.REMOVED,
                )

        while True:
            place = "lower"
            for k in range(-p, self.delta, 1):
                added = self.fp[(k - 1, p)].furthest_y + 1
                removed = self.fp[(k + 1, p - 1)].furthest_y
                set_fp(k, p, added, removed, place)

            place = "upper"
            for k in range(self.delta + p, self.delta, -1):
                added = self.fp[(k - 1, p - 1)].furthest_y + 1
                removed = self.fp[(k + 1, p)].furthest_y
                set_fp(k, p, added, removed, place)

            added = self.fp[(self.delta - 1, p)].furthest_y + 1
            removed = self.fp[(self.delta + 1, p)].furthest_y
            set_fp(self.delta, p, added, removed, "on")

            if self.fp[(self.delta, p)].furthest_y == self.N or p > 20:
                break
            p += 1
        self.P = p

    def _compose_ses(self):
        self.ses: List[DiffElement] = []
        # prefix
        for i in range(self.prefix_size):
            self.ses.append(
                DiffElement(
                    old_index=i,
                    new_index=i,
                    diff_type=DiffType.COMMON,
                )
            )

        # body
        if self.M == 0:
            for i in range(self.prefix_size, self.N + self.prefix_size):
                if self.swapped:
                    self.ses.append(
                        DiffElement(
                            old_index=i,
                            diff_type=DiffType.REMOVED,
                        )
                    )
                else:
                    self.ses.append(
                        DiffElement(
                            new_index=i,
                            diff_type=DiffType.ADDED,
                        )
                    )
        else:
            ses_body: List[DiffElement] = []
            cur = (self.delta, self.P)
            while cur != (0, 0):
                fp = self.fp[cur]

                for y in range(fp.furthest_y, fp.prev_y, -1):
                    if self.swapped:
                        ses_body.append(
                            DiffElement(
                                old_index=y - 1 + self.prefix_size,
                                new_index=y - cur[0] - 1 + self.prefix_size,
                                diff_type=DiffType.COMMON,
                            )
                        )
                    else:
                        ses_body.append(
                            DiffElement(
                                old_index=y - cur[0] - 1 + self.prefix_size,
                                new_index=y - 1 + self.prefix_size,
                                diff_type=DiffType.COMMON,
                            )
                        )
                if fp.diff_type == DiffType.ADDED:
                    if self.swapped:
                        ses_body.append(
                            DiffElement(
                                old_index=fp.prev_y - 1 + self.prefix_size,
                                diff_type=DiffType.REMOVED,
                            )
                        )
                    else:
                        ses_body.append(
                            DiffElement(
                                new_index=fp.prev_y - 1 + self.prefix_size,
                                diff_type=DiffType.ADDED,
                            )
                        )
                    cur = (cur[0] - 1, fp.prev_p)
                elif fp.diff_type == DiffType.REMOVED:
                    if self.swapped:
                        ses_body.append(
                            DiffElement(
                                new_index=fp.prev_y - cur[0] - 1 + self.prefix_size,
                                diff_type=DiffType.ADDED,
                            )
                        )
                    else:
                        ses_body.append(
                            DiffElement(
                                old_index=fp.prev_y - cur[0] - 1 + self.prefix_size,
                                diff_type=DiffType.REMOVED,
                            )
                        )
                    cur = (cur[0] + 1, fp.prev_p)
            self.ses.extend(reversed(ses_body))

        # suffix
        old_offset, new_offset = len(self.old) - len(self.suffix), len(self.new) - len(self.suffix)
        for i in range(len(self.suffix)):
            self.ses.append(
                DiffElement(
                    old_index=i + old_offset,
                    new_index=i + new_offset,
                    diff_type=DiffType.COMMON,
                )
            )


def compare(old: List[T], new: List[T], is_equal: Callable[[T, T], bool] = lambda a, b: a == b) -> List[DiffElement]:
    diffs = WuDiff(old, new, is_equal=is_equal)
    return diffs.ses
