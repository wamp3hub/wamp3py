import typing

import domain
import logger
import shared


PublishProcedure = typing.Callable

CallProcedure = typing.Callable


def PublishEventEndpoint(procedure):
    async def execute(publish_event: domain.PublishEvent):
        try:
            await procedure(publish_event)
        except Exception as e:
            logger.error('Publish', exception=repr(e))

    return execute


def CallEventEndpoint(procedure):
    async def execute(call_event: domain.CallEvent) -> domain.ReplyEvent | domain.ErrorEvent:
        reply_features = domain.ReplyFeatures(invocationID=call_event.ID)
        try:
            payload = await procedure(call_event)
            return domain.ReplyEvent(features=reply_features, payload=payload)
        except Exception as e:
            logger.error('call', exception=repr(e))
            return domain.ErrorEvent(
                features=reply_features, payload=domain.ErrorEventPayload(message=repr(e)),
            )

    return execute


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


def PieceByPieceEndpoint(procedure):
    async def execute(call_event: domain.CallEvent) -> PieceByPiece:
        generator = procedure(call_event)
        return PieceByPiece(generator)

    return execute

