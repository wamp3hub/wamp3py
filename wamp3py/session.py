import typing

from . import domain
from . import entrypoints
from . import logger
from . import shared


if typing.TYPE_CHECKING:
    from . import endpoints
    from . import peer


DEFAULT_TIMEOUT = 60


class RemoteGenerator:

    ID: str
    active: bool

    def __init__(
        self,
        router: 'peer.Peer',
        yield_event: domain.YieldEvent,
    ):
        self.active = True
        self._router = router
        self._last_yield_event = yield_event
        self.ID = yield_event['payload']['ID']

    async def stop(self):
        self.active = False
        stop_event = domain.new_stop_event({'invocationID': self.ID})
        await self._router.send(stop_event)

    async def next(
        self,
        timeout = DEFAULT_TIMEOUT,
    ) -> domain.YieldEvent | domain.ReplyEvent:
        self.active = False
        next_event = domain.new_next_event({'yieldID': self._last_yield_event['ID'], 'timeout': timeout})
        pending_yield_event = self._router.pending_reply_events.new(next_event['ID'])
        await self._router.send(next_event)
        response = await pending_yield_event
        if response['kind'] == domain.MessageKinds.Error.value:
            if response['payload']['message'] == 'GeneratorExit':
                raise StopAsyncIteration()
            raise domain.ApplicationError(response['payload']['message'])
        if response['kind'] == domain.MessageKinds.Yield.value:
            self._last_yield_event = response
            self.active = True
        return response

    async def __anext__(self):
        return await self.next()

    def __aiter__(self):
        return self


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
        router: 'peer.Peer',
    ):
        self._router = router
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
        return self._router.ID

    async def publish(
        self,
        URI: str,
        payload,
        /,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> domain.PublishEvent:
        """
        """
        if include is None:
            include = []
        if exclude is None:
            exclude = []
        publish_event = domain.new_publish_event(
            {'URI': URI, 'include': include, 'exclude': exclude},
            payload,
        )
        await self._router.send(publish_event)
        return publish_event

    async def call(
        self,
        URI: str,
        payload,
        /,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> domain.ReplyEvent | domain.YieldEvent:
        call_event = domain.new_call_event(
            {'URI': URI, 'timeout': timeout}, payload,
        )
        pending_reply_event = self._router.pending_reply_events.new(call_event['ID'])
        await self._router.send(call_event)
        response = await pending_reply_event
        if response['kind'] == domain.MessageKinds.Error.value:
            raise domain.ApplicationError(response['payload']['message'])
        # TODO generator
        return response

    async def subscribe(
        self,
        URI: str,
        procedure: 'endpoints.ProcedureToSubscribe',
    ) -> domain.Subscription:
        """
        """
        options: domain.SubscribeOptions = {'route': []}
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
    ) -> domain.Registration:
        """
        """
        options: domain.RegisterOptions = {'route': []}
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
