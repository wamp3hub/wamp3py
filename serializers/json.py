import json

import domain


class JSONSerializer:

    def encode(
        self,
        event: domain.Event,
    ) -> bytes:
        if not isinstance(event, domain.Event):
            raise Exception('InvalidEvent')
        raw_event = event.dump()
        message = json.dumps(raw_event)
        return message

    def decode(
        self,
        message: bytes,
    ) -> domain.Event:
        raw_event = json.loads(message)
        match raw_event['kind']:
            case domain.AcceptEvent.kind:
                event = domain.AcceptEvent()
            case domain.ReplyEvent.kind:
                event = domain.ReplyEvent()
            case domain.PublishEvent.kind:
                event = domain.PublishEvent()
            case domain.CallEvent.kind:
                event = domain.CallEvent()
            case _:
                raise Exception('InvalidEvent')
        event.load(raw_event)
        return event

