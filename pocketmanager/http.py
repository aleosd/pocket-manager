import asyncio
import json
import sys
import time
import urllib.request
from collections import defaultdict
from urllib.error import URLError

import aiohttp
import async_timeout
import click

from pocketmanager import config, const


async def check_status(session, link):
    with async_timeout.timeout(10):
        try:
            async with session.get(link.resolved_url) as response:
                return response.status, link
        except asyncio.TimeoutError:
            return -1, link
        except aiohttp.ClientConnectionError:
            return -2, link
        except asyncio.CancelledError:
            return -10, link
        except Exception:
            return -11, link


async def bound_fetch(sem, link, session):
    # Getter function with semaphore.
    async with sem:
        return await check_status(session, link)


async def check(links):
    sem = asyncio.Semaphore(100)

    tasks = []
    async with aiohttp.ClientSession() as session:
        for link in links:
            task = asyncio.ensure_future(bound_fetch(sem, link, session))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        return responses


def get_links_status(links):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(check(links))
    responses = loop.run_until_complete(future)

    results = defaultdict(list)
    for status, link in responses:
        results[status].append(link)
    return results


def get_links(since=None):
    data = {
        "consumer_key": config.api.consumer_key,
        "access_token": config.api.access_token,
        "state": "all",
        "detailType": "complete",
    }
    if since:
        data.update({'since': since})
    params = json.dumps(data).encode('utf8')
    req = urllib.request.Request(
        const.ARTICLES_GET_URL, method='POST', data=params,
        headers={'content-type': 'application/json'})
    try:
        click.echo('Querying pocket api for links data')
        r = urllib.request.urlopen(req).read()
    except URLError as e:
        click.secho(f'Error while querying pocket api {e}', fg='red')
        sys.exit(1)

    try:
        return json.loads(r.decode('utf-8'))
    except ValueError as e:
        click.secho(f'Error while parsing api response: {e}', fg='red')
        sys.exit(1)


def delete_link(link_id):
    current_timestamp = int(time.time())
    data = {
        "consumer_key": config.api.consumer_key,
        "access_token": config.api.access_token,
        "actions": [{
            "action": "delete",
            "item_id": str(link_id),
            "time": str(current_timestamp),
        }],
    }

    params = json.dumps(data).encode('utf8')
    req = urllib.request.Request(
        const.ARTICLES_CHANGE_URL, method='POST', data=params,
        headers={'content-type': 'application/json'})
    try:
        r = urllib.request.urlopen(req).read()
    except URLError as e:
        click.secho(f'Error while querying pocket api {e}', fg='red')
        return

    try:
        return json.loads(r.decode('utf-8'))
    except ValueError as e:
        click.secho(f'Error while parsing api response: {e}', fg='red')
        return
