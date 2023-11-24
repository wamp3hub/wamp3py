import typing

import domain
import endpoints
import peer
import shared


@shared.Domain
class NewResourcePayload:
    ID: str = shared.field(default_factory=shared.new_id)
    URI: str
    options: domain.RegisterOptions


@shared.Domain
class NewGeneratorPayload:
    ID: str = shared.field(default_factory=shared.new_id)


class Session:
    """
    """

    def __init__(
        self,
        peer: peer.Peer,
    ):
        self._peer = peer
        self._peer.incoming_publish_events.consume(self._on_publish)
        self._peer.incoming_call_events.consume(self._on_call)
        self._subscriptions = {}
        self._registrations = {}

    async def _on_publish(
        self,
        publish_event: domain.PublishEvent,
    ):
        """
        """
        endpoint = self._subscriptions.get(publish_event.route.endpointID)
        if endpoint is None:
            print('EndpointNotFound')
        else:
            await endpoint(publish_event)

    async def _on_yield(
        self,
        call_event: domain.CallEvent,
        endpoint: endpoints.GeneratorEndpoint,
    ):
        """
        """
        yield_event = await endpoint.execute(call_event)
        pending_stop_event = self._peer.pending_cancel_events.new(yield_event.payload.ID)

        while generator.active:
            pending_next_event = self._peer.pending_next_events.new(yield_event.ID)
            await self._peer.send(yield_event)
            [something], [pending] = await shared.select_first(
                pending_next_event,
                pending_stop_event,
            )
            match something:
                case next_event if domain.NextEvent():
                    pending_yield_event = generator.next(next_event)
                    [something], [pending] = await shared.select_first(
                        pending_yield_event,
                        pending_stop_event,
                    )
                    match something:
                        case domain.CancelEvent():
                            pending.cancel()
                case domain.CancelEvent():
                    pending.cancel()

    async def _on_call(
        self,
        call_event: domain.CallEvent,
    ):
        """
        """
        pending_cancel_event = self._peer.pending_cancel_events.new(call_event.ID)

        endpoint = self._registrations.get(call_event.route.endpointID)
        if endpoint is None:
            print('EndpointNotFound')
        elif endpoint.is_generator:
            await self._on_yield(call_event, endpoint)

        [something], [pending] = await shared.select_first(
            endpoint.execute(call_event),
            pending_cancel_event,
        )
        match something:
            case reply_event if domain.ReplyEvent():
                pending.cancel()
                await self._peer.send(reply_event)
                await self._on_yield(call_event, something)
            case domain.CancelEvent():
                pending.cancel()

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
        await self._peer.send(publish_event)

    async def call(
        self,
        URI: str,
        payload: typing.Any,
        timeout: int = 60,
    ) -> domain.ReplyEvent:
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
        pending_reply_event = self._peer.pending_reply_events.new(call_event.ID)
        await self._peer.send(call_event)
        reply_event = await pending_reply_event
        if isinstance(reply_event, domain.ErrorEvent):
            raise Exception(reply_event.payload.message)
        return reply_event

    async def subscribe(
        self,
        URI: str,
        options: domain.SubscribeOptions,
        procedure: endpoints.PublishProcedure,
    ) -> domain.Subscription:
        """
        """
        payload = NewResourcePayload(URI=URI, options=options)
        replyEvent = await self.call("wamp.router.subscribe", payload)
        subscription = shared.load(domain.Subscription, replyEvent.payload)
        self._subscriptions[subscription.ID] = procedure
        return subscription

    async def register(
        self,
        URI: str,
        options: domain.RegisterOptions,
        procedure: endpoints.CallProcedure,
    ) -> domain.Registration:
        """
        """
        payload = NewResourcePayload(URI=URI, options=options)
        replyEvent = await self.call("wamp.router.register", payload)
        registration = shared.load(domain.Registration, replyEvent.payload)
        self._registrations[registration.ID] = procedure
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
            self._registrations.pop(subscription_id)

    async def unregister(
        self,
        registration_id: str,
    ):
        """
        """
        try:
            await self.call("wamp.router.unregister", registration_id)
        finally:
            self._registrations.pop(registration_id)

    async def leave(
        self,
        reason: str,
    ):
        """
        """
        await self._peer.close()
