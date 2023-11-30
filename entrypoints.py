import typing

import domain
import endpoints
import shared


if typing.TYPE_CHECKING:
    import peer


class entrypoint:
    """
    """


class PublishEventEntrypoint(entrypoint):

    def __init__(
        self,
        procedure,
    ):
        self.endpoint = endpoints.PublishEventEndpoint(procedure)

    async def execute(
        self,
        router: 'peer.Peer',
        publish_event: domain.PublishEvent,
    ):
        await self.endpoint.execute(publish_event)


class CallEventEntrypoint(entrypoint):

    def __init__(
        self,
        procedure,
    ):
        self.endpoint = endpoints.CallEventEndpoint(procedure)

    async def execute(
        self,
        router: 'peer.Peer',
        call_event: domain.CallEvent,
    ):
        pending_cancel_event = router.pending_cancel_events.new(call_event.ID)

        something = await shared.select_first(
            self.endpoint.execute(call_event),
            pending_cancel_event,
        )

        if not isinstance(something, domain.CancelEvent):
            await router.send(something)


class PieceByPieceEntrypoint(entrypoint):

    def __init__(
        self,
        procedure,
    ):
        self.endpoint = endpoints.PieceByPieceEndpoint(procedure)

    async def execute(
        self,
        router: 'peer.Peer',
        call_event: domain.CallEvent,
    ):
        generator = await self.endpoint.execute(call_event)

        pending_stop_event = router.pending_cancel_events.new(generator.ID)

        yield_event = domain.YieldEvent(
            features=domain.ReplyFeatures(invocationID=call_event.ID),
            payload=domain.NewGeneratorPayload(ID=generator.ID),
        )

        while generator.active:
            pending_next_event = router.pending_next_events.new(yield_event.ID)

            await router.send(yield_event)

            something = await shared.select_first(
                pending_next_event,
                pending_stop_event,
                __cancel_pending=False,
            )

            if isinstance(something, domain.StopEvent):
                pending_next_event.cancel()
                break

            something = await shared.select_first(
                generator.next(something),
                pending_stop_event,
                __cancel_pending=False,
            )

            if isinstance(something, domain.YieldEvent):
                yield_event = something
                continue

            if not isinstance(something, domain.StopEvent):
                await router.send(something)

