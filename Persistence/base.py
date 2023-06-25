"The base of the extension."

from .persistence import Persistence

""" Commented out to make it work

version = Version(
    version="2.2.3",
    author=VersionAuthor(
        name="Dworv",
        email="dwarvyt@gmail.com",
    ),
)

base = Base(
    name="Persistence",
    version=version,
    link="https://github.com/dworv/interactions-persistence",
    description="An extension to add simple custom_id encoding to interactions.py.",
    packages="interactions.ext.Persistence",
)

"""

def setup(bot, cipher_key=None):
    return Persistence(bot, cipher_key)
