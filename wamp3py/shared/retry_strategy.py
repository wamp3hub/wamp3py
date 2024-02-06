import typing


class RetryAttemptsExceeded(StopIteration):
    """
    """


class RetryStrategy(typing.Protocol):
    """
    """

    attempt_number: int

    @property
    def done(self) -> bool:
        """
        """

    def next(self) -> int:
        """
        """

    def reset(self) -> None:
        """
        """


class ConstantRS(RetryStrategy):
    """
    """

    def __init__(
        self,
        delay: int,
        maximum_attempts: int,
    ) -> None:
        self.attempt_number = 0
        self._delay = delay
        self._maximum_attempts = maximum_attempts

    @property
    def done(self) -> bool:
        return self.attempt_number >= self._maximum_attempts

    def next(self) -> int:
        if self.done:
            raise RetryAttemptsExceeded()
        self.attempt_number += 1
        return self._delay

    def reset(self) -> None:
        self.attempt_number = 0


class BackoffRS(ConstantRS):
    """
    """

    def __init__(
        self,
        delay: int,
        maximum_attempts: int,
        factor: int,
        upper_bound: int,
    ) -> None:
        super().__init__(delay, maximum_attempts)
        self._maximum_attempts = maximum_attempts
        self._factor = factor
        self._upper_bound = upper_bound

    def next(self) -> int:
        d = super().next()
        v = self._factor ** (self.attempt_number - 1) - 1 + d
        if v > self._upper_bound:
            v = self._upper_bound
        return round(v)


DontRetryStrategy = ConstantRS(0, 0)

DefaultRetryStrategy = BackoffRS(0, 100, 3, 60)
