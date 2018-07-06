import time
import asyncio
import logging


class BaseRateLimiter:
    """
    Interface that must be implemented to satisfy naz's rate limiter.
    User implementations should inherit this class and
    implement the wait_for_token method with the type signatures shown.
    """

    async def wait_for_token(self) -> None:
        raise NotImplementedError("wait_for_token method must be implemented.")


class SimpleRateLimiter(BaseRateLimiter):
    """
    simple implementation of a token bucket rate limiting algo.
    https://en.wikipedia.org/wiki/Token_bucket
    todo: check that the algo actually works.

    Usage:
        rateLimiter = SimpleRateLimiter(logger=myLogger, SEND_RATE=10, MAX_TOKENS=25)
        await rateLimiter.wait_for_token()
        send_messsages()
    """

    def __init__(
        self,
        logger: logging.Logger,
        SEND_RATE: float = 1000,
        MAX_TOKENS: float = 1000,
        DELAY_FOR_TOKENS: float = 1,
    ) -> None:
        """
        :param SEND_RATE:                  (optional) [float]
            the maximum rate, in messages/second, at which naz can send messages to SMSC.
        :param MAX_TOKENS:                  (optional) [int]
            the total number of initial mesages naz can send before rate limiting kicks in.
        :param DELAY_FOR_TOKENS:                  (optional) [float]
            the duration in seconds which to wait for before checking for token availability after they had finished.
        """
        self.SEND_RATE: float = SEND_RATE
        self.MAX_TOKENS: float = MAX_TOKENS
        self.DELAY_FOR_TOKENS: float = (DELAY_FOR_TOKENS)
        self.tokens: float = self.MAX_TOKENS
        self.updated_at: float = time.monotonic()

        self.logger = logger

    async def wait_for_token(self) -> None:
        while self.tokens < 1:
            self.logger.info(
                "rate_limiting. SEND_RATE={0}. DELAY_FOR_TOKENS={1}".format(
                    self.SEND_RATE, self.DELAY_FOR_TOKENS
                )
            )
            self.add_new_tokens()
            # todo: sleep in an exponetial manner upto a maximum then wrap around.
            await asyncio.sleep(self.DELAY_FOR_TOKENS)
        self.tokens -= 1

    def add_new_tokens(self) -> None:
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.SEND_RATE
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now
