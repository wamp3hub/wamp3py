import inspect
import typing

import domain
import entrypoints
import logger
import shared


if typing.TYPE_CHECKING:
    import endpoints
    import peer


SECOND = 1000000000
DEFAULT_TIMEOUT = 60 * SECOND


class RemoteGenerator:

    ID: str

    @property
    def active(self) -> bool:
        return not self._done

    def __init__(
        self,
        router: 'peer.Peer',
        yield_event: domain.YieldEvent,
    ):
        self._done = False
        self._router = router
        self._last_yield_event = yield_event
        self._logger = logger
        payload = shared.load(domain.NewGeneratorPayload, yield_event.payload)
        self.ID = payload.ID

    async def stop(self):
        self._done = True
        stop_event = domain.StopEvent(
            features=domain.ReplyFeatures(invocationID=self.ID),
        )
        await self._router.send(stop_event)

    async def next(
        self,
        timeout = DEFAULT_TIMEOUT,
    ) -> domain.YieldEvent | domain.ReplyEvent:
        self._done = True
        next_event = domain.NextEvent(
            features=domain.NextFeatures(
                yieldID=self._last_yield_event.ID,
                timeout=timeout,
            ),
        )
        pending_yield_event = self._router.pending_reply_events.new(next_event.ID)
        await self._router.send(next_event)
        response = await pending_yield_event
        if isinstance(response, domain.ErrorEvent):
            if response.payload.message == 'GeneratorExit':
                raise StopAsyncIteration()
            raise Exception(response.payload.message)
        if isinstance(response, domain.YieldEvent):
            self._last_yield_event = response
            self._done = False
        return response

    async def __anext__(self):
        return await self.next()

    def __aiter__(self):
        return self


class Session:

    def __init__(
        self,
        router: 'peer.Peer',
    ):
        self._router = router
        self._entrypoints = {}
        self._logger = logger

        async def on_event(event: domain.PublishEvent | domain.CallEvent):
            entrypoint = self._entrypoints.get(event.route.endpointID)
            if entrypoint is None:
                self._logger.error('EntrypointNotFound', event=event)
                raise Exception('EntrypointNotFound')

            try:
                await entrypoint.execute(self._router, event)
            except Exception as e:
                self._logger.error('SomethingWentWrong', exception=repr(e), event=event)

        self._router.incoming_publish_events.observe(on_event)
        self._router.incoming_call_events.observe(on_event)

    async def publish(
        self,
        URI: str,
        payload: typing.Any,
    ) -> domain.PublishEvent:
        """
        """
        publish_event = domain.PublishEvent(
            ID=shared.new_id(),
            payload=payload,
            features=domain.PublishFeatures(
                URI=URI,
            ),
        )
        await self._router.send(publish_event)

    async def call(
        self,
        URI: str,
        payload: typing.Any,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> domain.ReplyEvent | RemoteGenerator:
        """
        """
        call_event = domain.CallEvent(
            ID=shared.new_id(),
            payload=payload,
            features=domain.CallFeatures(
                URI=URI,
                timeout=timeout,
            ),
        )
        pending_reply_event = self._router.pending_reply_events.new(call_event.ID)
        await self._router.send(call_event)
        response = await pending_reply_event
        if isinstance(response, domain.ErrorEvent):
            raise Exception(response.payload.message)
        if isinstance(response, domain.YieldEvent):
            return RemoteGenerator(self._router, response)
        return response

    async def subscribe(
        self,
        URI: str,
        options: domain.SubscribeOptions,
        procedure: 'endpoints.PublishProcedure',
    ) -> domain.Subscription:
        """
        """
        payload = domain.NewResourcePayload(URI=URI, options=options)
        reply_event = await self.call("wamp.router.subscribe", payload)
        subscription = shared.load(domain.Subscription, reply_event.payload)
        entrypoint = entrypoints.PublishEventEntrypoint(procedure)
        self._entrypoints[subscription.ID] = entrypoint
        return subscription

    async def register(
        self,
        URI: str,
        options: domain.RegisterOptions,
        procedure: 'endpoints.CallProcedure',
    ) -> domain.Registration:
        """
        """
        payload = domain.NewResourcePayload(URI=URI, options=options)
        reply_event = await self.call("wamp.router.register", payload)
        registration = shared.load(domain.Registration, reply_event.payload)
        if inspect.isasyncgenfunction(procedure):
            entrypoint = entrypoints.PieceByPieceEntrypoint(procedure)
        else:
            entrypoint = entrypoints.CallEventEntrypoint(procedure)
        self._entrypoints[registration.ID] = entrypoint
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

    async def leave(
        self,
        reason: str,
    ):
        """
        """
        await self._router.close()
