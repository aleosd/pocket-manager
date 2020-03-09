import click

from . import app, config, const


@click.group()
def cmd():
    config.load(const.CONFIG_PATH)


@click.command()
def reset():
    """Recreate all app data"""
    app.reset()


@click.command()
def stat():
    """Display statistic"""
    click.echo('Displaying pocket statistic')
    app.stat()


@click.command()
def init():
    """Create initial path/db file for app"""
    click.echo('Running initial steps')
    app.init()


@click.command()
def update():
    """Update links data"""
    app.update()


@click.command()
def display():
    """Run cli interface"""
    app.display()


@click.command()
def check():
    """Check http status of saved links"""
    app.check()


cmd.add_command(reset)
cmd.add_command(stat)
cmd.add_command(init)
cmd.add_command(update)
cmd.add_command(display)
cmd.add_command(check)
