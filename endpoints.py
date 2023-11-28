import typing

import domain
import logger
import shared


PublishProcedure = typing.Callable

CallProcedure = typing.Callable


class endpoint:

    def __init__(
        self,
        procedure: typing.Callable,
    ):
        self.procedure = procedure
        self._logger = logger


class PublishEventEndpoint(endpoint):

    async def execute(
        self,
        publish_event: domain.PublishEvent,
    ):
        try:
            await self.procedure(publish_event)
        except Exception as e:
            self._logger.error('Publish', exception=repr(e))


class CallEventEndpoint(endpoint):

    async def execute(
        self,
        call_event: domain.CallEvent,
    ) -> domain.ReplyEvent | domain.ErrorEvent:
        reply_features = domain.ReplyFeatures(invocationID=call_event.ID)
        try:
            payload = await self.procedure(call_event)
            return domain.ReplyEvent(features=reply_features, payload=payload)
        except Exception as e:
            self._logger.error('call', exception=repr(e))
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message=repr(e)),
            )


class PieceByPiece:

    ID: str

    @property
    def active(self) -> bool:
        return not self._done

    def __init__(
        self,
        generator
    ):
        self.ID = shared.new_id()
        self._done = False
        self._generator = generator
        self._logger = logger

    async def next(
        self,
        next_event: domain.NextEvent,
    ) -> domain.YieldEvent | domain.ReplyEvent | domain.ErrorEvent:
        reply_features = domain.ReplyFeatures(invocationID=next_event.ID)
        try:
            payload = await anext(self._generator)
            return domain.YieldEvent(features=reply_features, payload=payload)
        except (StopIteration, StopAsyncIteration):
            self._done = True
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message='GeneratorExit'),
            )
        except Exception as e:
            self._logger.error('next', exception=repr(e))
            self._done = True
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message=repr(e)),
            )


class PieceByPieceEndpoint(endpoint):

    async def execute(
        self,
        call_event: domain.CallEvent,
    ) -> PieceByPiece:
        generator = self.procedure(call_event)
        return PieceByPiece(generator)
