import json

import domain
import shared


class JSONSerializer:

    def encode(
        self,
        event: domain.Event,
    ) -> bytes:
        if not isinstance(event, domain.Event):
            raise Exception('InvalidEvent')
        raw_event = shared.dump(event)
        message = json.dumps(raw_event)
        return message

    def decode(
        self,
        message: bytes,
    ) -> domain.Event:
        raw_event = json.loads(message)
        match raw_event['kind']:
            case domain.MessageKinds.Accept:
                event = shared.load(domain.AcceptEvent, raw_event)
            case domain.MessageKinds.Reply | domain.MessageKinds.Error | domain.MessageKinds.Yield:
                event = shared.load(domain.ReplyEvent, raw_event)
            case domain.MessageKinds.Publish:
                event = shared.load(domain.PublishEvent, raw_event)
            case domain.MessageKinds.Call:
                event = shared.load(domain.CallEvent, raw_event)
            case _:
                raise Exception('InvalidEvent')
        return event

