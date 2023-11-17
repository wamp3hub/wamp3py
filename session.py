import inspect
import typing

import domain
import peer
import shared


@shared.Domain
class NewResourcePayload:
    ID: str
    URI: str
    options: domain.RegisterOptions


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
        procedure = self._subscriptions.get(publish_event.route.endpointID)
        if procedure is None:
            print('ProcedureNotFound')
        else:
            await procedure(publish_event)

    async def _on_yield(
        self,
        generator: typing.AsyncGenerator[domain.YieldEvent, None],
    ):
        """
        """
        async for yield_event in generator:
            pending_next_event = self._peer.pending_next_events.new(yield_event.ID)
            await self._peer.send(yield_event)
            await pending_next_event

    async def _on_call(
        self,
        call_event: domain.CallEvent,
    ):
        """
        """
        pending_cancel_event = self._peer.pending_cancel_events.new(call_event.ID)

        procedure = self._registrations.get(call_event.route.endpointID)
        if procedure is None:
            print('ProcedureNotFound')

        [something], [pending] = await shared.select_first(
            procedure(call_event),
            pending_cancel_event,
        )
        match something:
            case domain.ReplyEvent():
                if inspect.isasyncgen(something):
                    await self._on_yield(something)
                else:
                    pending.cancel()
                    await self._peer.send(something)
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
    ) -> domain.ReplyEvent:
        """
        """
        call_event = domain.CallEvent(
            ID=shared.new_id(),
            payload=payload,
            features=domain.CallFeatures(
                URI=URI,
                timeout=100,
            ),
        )

        pending_reply_event = self._peer.pending_reply_events.new(call_event.ID)
        await self._peer.send(call_event)
        reply_event = await pending_reply_event

        if isinstance(reply_event, domain.ErrorEvent):
            raise Exception(reply_event.payload.code)
        return reply_event

    async def register(
        self,
        URI: str,
        options: domain.RegisterOptions,
        procedure: domain.CallProcedure,
    ) -> domain.Registration:
        """
        """
        payload = NewResourcePayload(
            ID=shared.new_id(),
            URI=URI,
            options=options,
        )
        replyEvent = await self.call("wamp.router.register", payload)
        registration = shared.load(domain.Registration, replyEvent.payload)
        self._registrations[registration.ID] = procedure
        return registration

    async def subscribe(
        self,
        URI: str,
        options: domain.SubscribeOptions,
        procedure: domain.PublishProcedure,
    ) -> domain.Subscription:
        """
        """
        payload = NewResourcePayload(
            ID=shared.new_id(),
            URI=URI,
            options=options,
        )
        replyEvent = await self.call("wamp.router.subscribe", payload)
        subscription = shared.load(domain.Subscription, replyEvent.payload)
        self._subscriptions[subscription.ID] = procedure
        return subscription

    async def unregister(
        self,
        registration_id: str,
    ):
        """
        """
        await self.call("wamp.router.unregister", registration_id)
        self._registrations.pop(registration_id)

    async def unsubscribe(
        self,
        subscription_id: str,
    ):
        """
        """
        await self.call("wamp.router.unsubscribe", subscription_id)
        self._registrations.pop(subscription_id)

    async def leave(
        self,
        reason: str,
    ):
        """
        """
        await self._peer.close()
