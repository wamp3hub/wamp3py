import typing

import httpx

from ... import domain


class InterviewFail(Exception):
    """
    """


class SuccessPayload(domain.Domain):
    routerID: str
    yourID: str
    ticket: str


async def http2interview(
    address: str,
    secure: bool,
    credentials: typing.Any,
) -> SuccessPayload:
    async with httpx.AsyncClient() as client:
        protocol = 'http'
        if secure:
            protocol = 'https'
        url = f'{protocol}://{address}/wamp/v1/interview'
        request_json = { 'credentials': credentials }
        response = await client.post(url, json=request_json)
        if response.status_code == 200:
            response_json = response.json()
            response_payload = response_json
            return response_payload
        if response.status_code == 400:
            response_json = response.json()
            error_message = response_json.get('code') or 'UnknownError'
            raise InterviewFail(error_message)
        raise InterviewFail(f'{response.status_code}: {response.text}')

