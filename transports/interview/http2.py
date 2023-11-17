import typing

import aiohttp

import shared


@shared.Domain
class ErrorPayload:
    code: str


@shared.Domain
class SuccessPayload:
    routerID: str
    yourID: str
    ticket: str


async def http2interview(
    address: str,
    secure: bool,
    credentials: typing.Any,
) -> SuccessPayload:
    async with aiohttp.ClientSession() as session:
        protocol = 'http'
        if secure:
            protocol = 'https'
        url = f'{protocol}://{address}/wamp/v1/interview'
        request_json = { 'credentials': credentials }
        async with session.post(url, json=request_json) as response:
            response_json = await response.json()
            if response.status == 200:
                response_payload = shared.load(SuccessPayload, response_json)
                return response_payload
            response_payload = shared.load(ErrorPayload, response_json)
            raise Exception(response_payload.code)
