from setuptools import setup, find_packages


setup(
    name="pocketmanager",
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Click', 'aiohttp', 'async_timeout', 'confj'
    ],
    entry_points='''
    [console_scripts]
    pocketmanager=pocketmanager.cli:cmd
    ''',
)
