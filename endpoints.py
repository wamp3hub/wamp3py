import asyncio
import inspect
import typing

import domain
import logger


CallProcedure = typing.Callable

PublishProcedure = typing.Callable


class endpoint:
    """
    """

    def __init__(
        self,
        procedure: CallProcedure,
    ):
        self._procedure = procedure


class PublishEndpoint(endpoint):
    """
    """

    async def execute(
        self,
        publish_event: domain.PublishEvent,
    ):
        try:
            await self._procedure(publish_event)
        except Exception as e:
            logger.error('PublishError', exception=repr(e))


class CallEndpoint(endpoint):
    """
    """

    async def execute(
        self,
        call_event: domain.CallEvent,
    ) -> domain.ReplyEvent | domain.ErrorEvent:
        try:
            async with asyncio.timeout(call_event.features.timeout):
                payload = await self._procedure(call_event)
                reply_event = domain.ReplyEvent(
                    features=domain.ReplyFeatures(invocationID=call_event.ID),
                    payload=payload,
                )
                return reply_event
        # except asyncio.TimeoutError:
        #     logger.error('CallTimedout')
        #     error_event = domain.ErrorEvent(
        #         features=domain.ReplyFeatures(invocationID=call_event.ID),
        #         payload=domain.ErrorEventPayload(message='Timedout'),
        #     )
        #     return error_event
        # except asyncio.CancelledError:
        #     logger.error('CallCancelled')
        #     error_event = domain.ErrorEvent(
        #         features=domain.ReplyFeatures(invocationID=call_event.ID),
        #         payload=domain.ErrorEventPayload(message='Cancelled'),
        #     )
        #     return error_event
        except Exception as e:
            logger.error('CallError', exception=repr(e))
            error_event = domain.ErrorEvent(
                features=domain.ReplyFeatures(invocationID=call_event.ID),
                payload=domain.ErrorEventPayload(message=repr(e)),
            )
            return error_event


class GeneratorEndpoint(endpoint):
    """
    """

    async def execute(
        self,
        call_event: domain.CallEvent,
    ) -> domain.YieldEvent:
        self._generator = await self._procedure(call_event)
        yield_event = domain.YieldEvent(
            features=domain.ReplyFeatures(invocationID=call_event.ID),
            payload=NewGeneratorPayload(),
        )
        return yield_event

    @property
    def active(self) -> bool:
        return True

    async def next(
        self,
        next_event: domain.NextEvent
    ) -> domain.YieldEvent | domain.ReplyEvent | domain.ErrorEvent:
        try:
            async with asyncio.timeout(next_event.features.timeout):
                payload = await anext(self._generator, next_event)
                yield_event = domain.YieldEvent(
                    features=domain.ReplyFeatures(invocationID=next_event.ID),
                    payload=payload,
                )
                return yield_event
        except Exception as e:
            logger.error('NextError', exception=repr(e))
            error_event = domain.ErrorEvent(
                features=domain.ReplyFeatures(invocationID=next_event.ID),
                payload=domain.ErrorEventPayload(message=repr(e)),
            )
            return error_event

