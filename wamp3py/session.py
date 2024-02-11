import typing

from . import domain
from . import entrypoints
from . import logger
from . import shared


if typing.TYPE_CHECKING:
    from . import endpoints
    from . import peer


DEFAULT_TIMEOUT = 60


async def new_remote_generator(
    peer: 'peer.Peer',
    streamID: str,
) -> typing.AsyncGenerator[typing.Any, domain.SubEvent]:
    def on_stop(_):
        # TODO check
        raise StopAsyncIteration()

    pending_stop_event = peer.pending_reply_events.new(streamID)
    pending_stop_event.add_done_callback(on_stop)

    async for yield_event in peer.incoming_subevents.as_iterator():
        if yield_event['streamID'] != streamID:
            continue

        payload = yield yield_event

        next_event = domain.new_subevent(streamID, payload)
        await peer.send(next_event)

    pending_stop_event.cancel()


class newResourcePayload(domain.Domain):
    ID: str
    URI: str


class subscribePayload(newResourcePayload):
    options: domain.SubscribeOptions


class registerPayload(newResourcePayload):
    options: domain.RegisterOptions


class Session:

    def __init__(
        self,
        peer: 'peer.Peer',
    ):
        self._router = peer
        self._entrypoints = {}
        self._restores = {}

        async def on_event(event: domain.Publication | domain.Invocation):
            entrypoint = self._entrypoints.get(event['route']['endpointID'])
            if callable(entrypoint):
                try:
                    await entrypoint(self._router, event)
                except Exception as e:
                    logger.error('something went wrong', exception=repr(e), event=event)
            else:
                logger.error('entrypoint not found', event=event)

        self._router.incoming_publish_events.observe(on_event)
        self._router.incoming_call_events.observe(on_event)

        async def rejoin(_):
            logger.warn('rejoining...')
            for restore in self._restores.values():
                await restore()

        async def on_leave():
            logger.warn('leaving...')
            self._restores = {}
            self._entrypoints = {}

        self._router.rejoin_events.observe(rejoin, on_leave)

    @property
    def ID(self) -> str:
        return self._router.details['ID']

    @property
    def role(self) -> str:
        return self._router.details['role']

    async def publish(
        self,
        URI: str,
        payload,
        /,
        include_subscribers: list[str] | None = None,
        include_roles: list[str] | None = None,
        exclude_subscribers: list[str] | None = None,
        exclude_roles: list[str] | None = None,
    ) -> domain.PublishEvent:
        """
        """
        if include_subscribers is None:
            include_subscribers = []
        if include_roles is None:
            logger.warn('fill in the list of allowed subscriber roles for security reasons')
            include_roles = []
        if exclude_subscribers is None:
            exclude_subscribers = []
        if exclude_roles is None:
            exclude_roles = []
        publish_features: domain.PublishFeatures = {
            'URI': URI,
            'includeSubscribers': include_subscribers,
            'includeRoles': include_roles,
            'excludeSubscribers': exclude_subscribers,
            'excludeRoles': exclude_roles,
        }
        publish_event = domain.new_publish_event(publish_features, payload)
        await self._router.send(publish_event)
        return publish_event

    async def call(
        self,
        URI: str,
        payload,
        /,
        timeout: int = DEFAULT_TIMEOUT,
        include_roles: list[str] | None = None,
        exclude_roles: list[str] | None = None,
    ) -> domain.ReplyEvent:
        if include_roles is None:
            logger.warn('fill in the list of allowed executor roles for security reasons')
            include_roles = []
        if exclude_roles is None:
            exclude_roles = []
        call_features: domain.CallFeatures = {
            'URI': URI,
            'timeout': timeout,
            'includeRoles': include_roles,
            'excludeRoles': exclude_roles,
        }
        call_event = domain.new_call_event(call_features, payload)
        pending_reply_event = self._router.pending_reply_events.new(call_event['ID'])
        await self._router.send(call_event)
        response = await pending_reply_event
        if response['kind'] == domain.MessageKinds.Error.value:
            raise domain.ApplicationError(response['payload']['message'])
        return response

    async def subscribe(
        self,
        URI: str,
        procedure: 'endpoints.ProcedureToSubscribe',
        /,
        include_roles: list[str] | None = None,
        exclude_roles: list[str] | None = None,
    ) -> domain.Subscription:
        if include_roles is None:
            logger.warn('fill in the list of allowed subscriber roles for security reasons')
            include_roles = []
        if exclude_roles is None:
            exclude_roles = []
        options: domain.SubscribeOptions = {
            'includeRoles': include_roles,
            'excludeRoles': exclude_roles,
            'route': [],
        }
        payload: subscribePayload = {'ID': shared.new_id(), 'URI': URI, 'options': options}
        reply_event = await self.call("wamp.router.subscribe", payload)
        subscription: domain.Subscription = reply_event['payload']

        async def restore():
            self._entrypoints.pop(subscription['ID'])
            await self.subscribe(URI, procedure)

        self._restores[subscription['ID']] = restore

        entrypoint = entrypoints.PublishEventEntrypoint(procedure)
        self._entrypoints[subscription['ID']] = entrypoint

        return subscription

    async def register(
        self,
        URI: str,
        procedure: 'endpoints.ProcedureToRegister',
        /,
        include_roles: list[str] | None = None,
        exclude_roles: list[str] | None = None,
    ) -> domain.Registration:
        if include_roles is None:
            logger.warn('fill in the list of allowed caller roles for security reasons')
            include_roles = []
        if exclude_roles is None:
            exclude_roles = []
        options: domain.RegisterOptions = {
            'includeRoles': include_roles,
            'excludeRoles': exclude_roles,
            'route': [],
        }
        payload: registerPayload = {'ID': shared.new_id(), 'URI': URI, 'options': options}
        reply_event = await self.call("wamp.router.register", payload)
        registration: domain.Registration = reply_event['payload']

        async def restore():
            self._entrypoints.pop(registration['ID'])
            await self.register(URI, procedure)

        self._restores[registration['ID']] = restore

        entrypoint = entrypoints.CallEventEntrypoint(procedure)
        self._entrypoints[registration['ID']] = entrypoint

        return registration

    async def unsubscribe(
        self,
        subscription_id: str,
    ):
        """
        """
        try:
            await self.call("wamp.router.unsubscribe", subscription_id)
        finally:
            self._entrypoints.pop(subscription_id)
            self._restores.pop(subscription_id)

    async def unregister(
        self,
        registration_id: str,
    ):
        """
        """
        try:
            await self.call("wamp.router.unregister", registration_id)
        finally:
            self._entrypoints.pop(registration_id)
            self._restores.pop(registration_id)

    async def leave(
        self,
        reason: str,
    ):
        """
        """
        # TODO send goodbye
        await self._router.close()
