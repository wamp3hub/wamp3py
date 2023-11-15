import asyncio
import typing


class Stream:

    _procedures: typing.List[typing.Callable]

    async def consume(
        self,
        procedure: typing.Callable,
    ):
        self._procedures.append(procedure)

    async def produce(
        self,
        *args,
        **kwargs,
    ):
        async with asyncio.TaskGroup() as tg:
            for procedure in self._procedures:
                coro = procedure(*args, **kwargs)
                tg.create_task(coro)

