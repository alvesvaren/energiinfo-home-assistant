"""Sample API Client."""
import logging
import asyncio
import socket
from typing import Any, Coroutine, Optional
import aiohttp
import async_timeout

TIMEOUT = 10


_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {
    "Content-type": "application/json; charset=UTF-8",
}

ENTRY_POINT = "https://api4.energiinfo.se/"


class IntegrationBlueprintApiClient:
    def __init__(
        self,
        username: str,
        password: str,
        meter_id: str,
        site_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Energiinfo API Client."""
        self._username = username
        self._password = password
        self._meter_id = meter_id
        self._site_id = site_id
        self._session = session
        self._access_token = None

    async def _get_access_token(self):
        if self._access_token:
            return self._access_token
        resp = await self.fetch(
            "login",
            params={
                "username": self._username,
                "password": self._password,
                "site": self._site_id,
                "type": "permanent",
            },
        )

        if resp:
            data = await resp.json()
            self._access_token = data["access_token"]

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        return (
            await self.fetch(
                "period",
                {
                    "period": 202108,
                    "signal": "ActiveEnergy",
                    "interval": "hour",
                    "count": 24,
                },
            )
            or {}
        )

    # async def async_set_title(self, value: str) -> None:
    #     """Get data from the API."""
    #     url = "https://jsonplaceholder.typicode.com/posts/1"
    #     await self.api_wrapper("patch", url, data={"title": value}, headers=HEADERS)

    async def fetch(self, cmd: str, params: dict = {}, headers: dict = {}):
        """Get information from the API."""
        try:
            async with async_timeout.timeout(TIMEOUT, loop=asyncio.get_event_loop()):
                resp = await self._session.get(
                    ENTRY_POINT,
                    params={
                        "access_token": "none"
                        if cmd == "login"
                        else self._access_token,
                        "meter_id": self._meter_id,
                        **params,
                    },
                    headers={**HEADERS, **headers},
                )

                return await resp.json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                f"Timeout error fetching information from energiinfo: {cmd} with {params}",
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                f"Error parsing information from energiinfo: {cmd} with {params}",
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                f"Error fetching information from energiinfo: {cmd} with {params}",
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
