import typing

import domain
import shared


if typing.TYPE_CHECKING:
    import endpoints
    import peer


class entrypoint:

    def __init__(
        self,
        endpoint,
    ):
        self.endpoint = endpoint


class PublishEventEntrypoint(entrypoint):

    endpoint: 'endpoints.PublishEventEndpoint'

    async def execute(
        self,
        router: 'peer.Peer',
        publish_event: domain.PublishEvent,
    ):
        await self.endpoint.execute(publish_event)


class CallEventEntrypoint(entrypoint):

    endpoint: 'endpoints.CallEventEndpoint'

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

    endpoint: 'endpoints.PieceByPieceEndpoint'

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

