import sys
import time
from curses import wrapper

import click
from pathlib import Path

from . import const
from . import database
from . import http


def init():
    """Initialise app: create app data directory and database file"""

    if not const.APP_DATA_DIR.exists():
        click.echo(f'Creating app home directory at {const.APP_DATA_DIR}')
        Path.mkdir(const.APP_DATA_DIR, mode=0o700)

    if const.DATABASE_PATH.exists():
        click.secho('ERROR: Database file already exists, try "pocketmanager '
                    'reset" to fully recreate it', fg='red')
        sys.exit(1)
    const.STATE_FILE.touch()
    click.echo(f'Creating database file {const.DATABASE_PATH}')
    database.init()


def reset():
    """Recreate all system files"""
    if const.STATE_FILE.exists():
        const.STATE_FILE.unlink()
    if const.DATABASE_PATH.exists():
        const.DATABASE_PATH.unlink()
    init()


def update():
    """Update saved in pocket links data in local database"""
    current_timestamp = int(time.time())
    last_timestamp = const.STATE_FILE.read_text()
    response = http.get_links(since=last_timestamp)
    links = response['list']
    link_count = len(links)
    click.echo(f'{link_count} links changed, loading them to database')
    created_count = 0
    for link_code in links:
        _, created = database.add_link(links[link_code])
        if created:
            created_count += 1
    click.secho(f'Successfully loaded {link_count} links to database: '
                f'{created_count} new, {link_count - created_count} updated')
    deleted = database.remove_deleted()
    if deleted > 0:
        click.secho(f'Removed {deleted} links')
    const.STATE_FILE.write_text(str(current_timestamp))


def stat():
    """Prints links statistic info"""
    stat_data = database.stat()
    click.secho(f'Total links: {stat_data["total"]}', bold=True)
    click.secho(f'Unread links: {stat_data["unread"]}', bold=True)
    click.secho(f'Archived links: {stat_data["archived"]}', bold=True)


def check():
    """Checks http status (availability) of saved links"""
    click.secho(f'Checking http-status of saved links...')
    links_by_status = http.get_links_status(database.get_records())
    click.secho(f'Updating links data in database')
    for status, links in links_by_status.items():
        click.secho(f'Writing data for status {status}')
        for link in links:
            link.update_check_result(status)
    click.secho(f'Done!')


def display():
    from . import interface
    wrapper(interface.Window)
