import json

from .. import domain
from .. import peer


class JSONSerializer(peer.Serializer):

    def encode(
        self,
        event: domain.Event,
    ) -> bytes:
        message = json.dumps(event)
        return message.encode()

    def decode(
        self,
        message: bytes | str,
    ) -> domain.Event:
        event = json.loads(message)
        return event

