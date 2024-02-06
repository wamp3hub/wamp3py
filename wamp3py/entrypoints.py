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
        logger.debug('new publish')

        await endpoint(publish_event)

    return execute


def CallEventEntrypoint(procedure):
    endpoint = endpoints.CallEventEndpoint(procedure)

    async def execute(
        router: 'peer.Peer',
        call_event: domain.Invocation,
    ):
        logger.debug('new call')

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
