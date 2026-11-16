"""Interest rates that know whether they include inflation.

A 6% return above inflation and a 6% loan rate are not the same thing. Every rate
in the model is a ``Rate`` carrying a basis:

* REAL: above inflation, in today's rands.
* NOMINAL: in money terms, inflation included. Loan rates are quoted this way.

Comparing two rates on different bases raises ``BasisMismatchError``, so a
real-versus-nominal comparison cannot happen by accident.

"Nominal" has a second meaning in finance: a quoted annual rate that ignores
compounding within the year. To avoid confusion, every ``Rate`` value is an
*effective annual* rate, and quoted loan rates are converted on the way in with
``Rate.from_quoted_monthly``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Basis(str, Enum):
    REAL = "real"
    NOMINAL = "nominal"


class BasisMismatchError(TypeError):
    """Raised when a real rate meets a nominal one."""


@dataclass(frozen=True)
class Rate:
    value: float  # effective annual rate, e.g. 0.04 for 4%
    basis: Basis

    @classmethod
    def real(cls, value: float) -> Rate:
        return cls(value, Basis.REAL)

    @classmethod
    def nominal(cls, value: float) -> Rate:
        return cls(value, Basis.NOMINAL)

    @classmethod
    def from_quoted_monthly(cls, quoted_annual: float) -> Rate:
        """A loan rate quoted per year but charged monthly, as an effective rate."""
        return cls((1 + quoted_annual / 12) ** 12 - 1, Basis.NOMINAL)

    def to_real(self, inflation: float) -> Rate:
        """Strip out inflation: (1 + nominal) = (1 + real) x (1 + inflation)."""
        if self.basis is Basis.REAL:
            return self
        return Rate((1 + self.value) / (1 + inflation) - 1, Basis.REAL)

    def to_nominal(self, inflation: float) -> Rate:
        if self.basis is Basis.NOMINAL:
            return self
        return Rate((1 + self.value) * (1 + inflation) - 1, Basis.NOMINAL)

    def require(self, basis: Basis) -> Rate:
        """Return self, or fail loudly if the rate is on the wrong basis."""
        if self.basis is not basis:
            raise BasisMismatchError(
                f"expected a {basis.value} rate, got a {self.basis.value} one"
            )
        return self

    def growth(self, years: float) -> float:
        """What R1 becomes after ``years`` at this rate."""
        return (1 + self.value) ** years

    def _same_basis(self, other: Rate) -> None:
        if not isinstance(other, Rate):
            raise TypeError("a Rate can only be compared with another Rate")
        if self.basis is not other.basis:
            raise BasisMismatchError(
                f"cannot compare a {self.basis.value} rate with a "
                f"{other.basis.value} rate; convert one of them first"
            )

    def __lt__(self, other: Rate) -> bool:
        self._same_basis(other)
        return self.value < other.value

    def __le__(self, other: Rate) -> bool:
        self._same_basis(other)
        return self.value <= other.value

    def __gt__(self, other: Rate) -> bool:
        self._same_basis(other)
        return self.value > other.value

    def __ge__(self, other: Rate) -> bool:
        self._same_basis(other)
        return self.value >= other.value
