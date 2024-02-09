import typing

import httpx

from .. import domain


class InterviewFail(Exception):
    """
    """


class Resume[T: typing.Any](domain.Domain):
    role: str
    credentials: T


class Offer(domain.Domain):
    registrationsLimit: int
    subscriptionsLimit: int
    ticketLifeTime: int


class Result(domain.Domain):
    routerID: str
    yourID: str
    offer: Offer
    ticket: str


async def http2interview(
    address: str,
    secure: bool,
    resume: Resume,
) -> Result:
    async with httpx.AsyncClient() as client:
        protocol = 'http'
        if secure:
            protocol = 'https'
        url = f'{protocol}://{address}/wamp/v1/interview'
        response = await client.post(url, json=resume)
        if response.status_code == 200:
            response_json = response.json()
            return response_json
        if response.status_code == 400:
            response_json = response.json()
            error_message = response_json.get('code') or 'UnknownError'
            raise InterviewFail(error_message)
        raise InterviewFail(f'{response.status_code}: {response.text}')

