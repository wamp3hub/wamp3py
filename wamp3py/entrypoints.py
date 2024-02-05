import typing

from . import domain
from . import endpoints
from . import logger


if typing.TYPE_CHECKING:
    from . import peer


def PublishEventEntrypoint(procedure):
    endpoint = endpoints.PublishEventEndpoint(procedure)

    async def execute(
        router: 'peer.Peer',
        publish_event: domain.Publication
    ):
        logger.debug('publish')

        await endpoint(publish_event)

    return execute


def CallEventEntrypoint(procedure):
    endpoint = endpoints.CallEventEndpoint(procedure)

    async def execute(
        router: 'peer.Peer',
        call_event: domain.Invocation,
    ):
        logger.debug('call')

        pending_response = endpoint(call_event)

        pending_cancel_event = router.pending_cancel_events.new(call_event['ID'])
        pending_cancel_event.add_done_callback(
            lambda _: pending_response.close()
        )

        try:
            response = await pending_response
        except Exception as e:
            logger.error("during execute procedure", exception=repr(e))
        else:
            pending_cancel_event.cancel()
            await router.send(response)

    return execute


def PieceByPieceEntrypoint(procedure):
    endpoint = endpoints.PieceByPieceEndpoint(procedure)

    async def execute(
        router: 'peer.Peer',
        call_event: domain.Invocation,
    ):
        logger.debug('call piece by piece')

        generator = endpoint(call_event)

        pending_stop_event = router.pending_cancel_events.new(generator.ID)
        pending_stop_event.add_done_callback(
            lambda _: generator.stop()
        )

        yield_event = domain.new_yield_event(
            {'invocationID': call_event['ID']},
            {'ID': generator.ID},
        )

        while generator.active:
            # FIXME if stop event appear
            pending_next_event = router.pending_next_events.new(yield_event['ID'])

            await router.send(yield_event)

            next_event = await pending_next_event

            response = await generator.next(next_event)

            if response['kind'] == domain.MessageKinds.Yield.value:
                yield_event = response
                continue

            await router.send(response)

        pending_stop_event.cancel()

    return execute
