import json

from .. import domain
from .. import peer
from .. import shared


class JSONSerializer:

    def encode(
        self,
        event: domain.Event,
    ) -> bytes:
        if not isinstance(event, domain.Event):
            raise peer.SerializationFail('InvalidEvent')
        raw_event = shared.dump(event)
        message = json.dumps(raw_event)
        return message

    def decode(
        self,
        message: bytes | str,
    ) -> domain.Event:
        raw_event = json.loads(message)
        match raw_event['kind']:
            case domain.MessageKinds.Accept:
                event = shared.load(domain.AcceptEvent, raw_event)
            case domain.MessageKinds.Reply:
                event = shared.load(domain.ReplyEvent, raw_event)
            case domain.MessageKinds.Error:
                event = shared.load(domain.ErrorEvent, raw_event)
            case domain.MessageKinds.Yield:
                event = shared.load(domain.YieldEvent, raw_event)
            case domain.MessageKinds.Publish:
                event = shared.load(domain.PublishEvent, raw_event)
            case domain.MessageKinds.Call:
                event = shared.load(domain.CallEvent, raw_event)
            case domain.MessageKinds.Next:
                event = shared.load(domain.NextEvent, raw_event)
            case domain.MessageKinds.Cancel:
                event = shared.load(domain.CancelEvent, raw_event)
            case _:
                raise peer.SerializationFail('InvalidEvent')
        return event

