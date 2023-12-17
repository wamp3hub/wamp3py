import typing

from . import domain
from . import endpoints
from . import logger
from . import shared


if typing.TYPE_CHECKING:
    import peer


def PublishEventEntrypoint(procedure):
    endpoint = endpoints.PublishEventEndpoint(procedure)

    async def execute(
        router: 'peer.Peer',
        publish_event: domain.PublishEvent
    ):
        logger.debug('publish')

        await endpoint(publish_event)

    return execute


def CallEventEntrypoint(procedure):
    endpoint = endpoints.CallEventEndpoint(procedure)

    async def execute(
        router: 'peer.Peer',
        call_event: domain.CallEvent,
    ):
        logger.debug('call')

        pending_cancel_event = router.pending_cancel_events.new(call_event.ID)

        something = await shared.race(
            endpoint(call_event),
            pending_cancel_event,
        )

        if not isinstance(something, domain.CancelEvent):
            pending_cancel_event.cancel()
            await router.send(something)

    return execute


@shared.Domain
class NewGeneratorPayload:
    ID: str


def PieceByPieceEntrypoint(procedure):
    endpoint = endpoints.PieceByPieceEndpoint(procedure)

    async def execute(
        router: 'peer.Peer',
        call_event: domain.CallEvent,
    ):
        logger.debug('call piece by piece')

        generator = await endpoint(call_event)

        pending_stop_event = router.pending_cancel_events.new(generator.ID)

        yield_event = domain.YieldEvent(
            features=domain.ReplyFeatures(invocationID=call_event.ID),
            payload=NewGeneratorPayload(ID=generator.ID),
        )

        active = True
        while active:
            pending_next_event = router.pending_next_events.new(yield_event.ID)

            await router.send(yield_event)

            something = await shared.race(
                pending_next_event,
                pending_stop_event,
                __cancel_pending=False,
            )

            if isinstance(something, domain.StopEvent):
                pending_next_event.cancel()
                break

            something = await shared.race(
                generator.next(something),
                pending_stop_event,
                __cancel_pending=False,
            )

            if isinstance(something, domain.YieldEvent):
                yield_event = something
                continue

            if not isinstance(something, domain.StopEvent):
                pending_stop_event.cancel()
                await router.send(something)

            active = False

    return execute

