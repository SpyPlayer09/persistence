"""The main file containing the Persistence extension."""

from json import JSONDecodeError
import logging
from types import MethodType
from typing import Callable, Dict, Tuple, Union

import interactions
from interactions import Extension, ModalContext, ComponentContext, listen
from interactions.api.events import Component

from .cipher import Cipher
from .client import persistent_component, persistent_modal
from .parse import PersistentCustomID


class Persistence(Extension):
    """
    The Persistence extension.

    The Persistence extension handles the persistent custom_ids. It is a simple extension that makes adding information to custom_ids simple and easy.
    """

    def __init__(self, bot, cipher_key=None):
        """
        The constructor for the Persistence extension.

        Parameters:
            bot (interactions.Client): The client instance.
            cipher_key (str): The cipher key to use. When not provided, a random key will be generated and components will never persist restarts.
                (default is None)
        """
        self._cipher = Cipher(cipher_key)

        #TODO: Decide whether the following should stay typehinted or not.
        self._component_callbacks: Dict[str, Callable[[ComponentContext, Union[str, int, float, list, dict]], None]] = {}
        self._modal_callbacks: Dict[str, Tuple[Callable[[ComponentContext, Union[str, int, float, list, dict]], None], bool]] = {}

        # set as bot.Persistence for convenience
        bot.persistence = self

        bot.persistent_component = MethodType(persistent_component, bot)
        bot.persistent_modal = MethodType(persistent_modal, bot)

    def component(self, tag: str):
        """
        The persistent component decorator.

        Parameters:
            tag (str): The tag to identify your component.
        """

        def inner(coro):
            self._component_callbacks[tag] = coro
            logging.debug(f"Registered persistent component: {tag}")
            return coro

        return inner

    def modal(self, tag: str, use_kwargs: bool = False):
        """
        The persistent modal decorator.

        Parameters:
            tag (str): The tag to identify your modal.
            use_kwargs (bool): Whether to return key word arguments mapped with the custom_ids of the individual text inputs. Not recommended.
                (defaults to False)
        """

        def inner(coro):
            self._modal_callbacks[tag] = (coro, use_kwargs)
            logging.debug(f"Registered persistent modal: {tag}")
            return coro

        return inner

    @listen()
    async def on_component(self, ctx: Component):
        """The on_component listener. This is called when a component is used."""
        ctx = ctx.ctx
        if not any((
            ctx.custom_id.startswith("p~"),
            ctx.custom_id[0] == "p" and ctx.custom_id[2] == "~"
        )):
            print("Silent fail")
            return

        try:
            pid = PersistentCustomID.from_discord(self._cipher, ctx.custom_id)
        except JSONDecodeError:
            logging.info("Interaction made with invalid persistent custom_id. Skipping.")
            return

        if pid.tag in self._component_callbacks:
            if ctx.values:
                await self._component_callbacks[pid.tag](ctx, pid.package, ctx.values)
            else:
                await self._component_callbacks[pid.tag](ctx, pid.package)

    @listen()
    async def on_modal(self, ctx: ModalContext):
        """The on_modal listener. This is called when a modal is submitted."""
        if not any((
            ctx.custom_id.startswith("p~"),
            ctx.custom_id[0] == "p" and ctx.custom_id[2] == "~"
        )):
            return

        try:
            pid = PersistentCustomID.from_discord(self._cipher, ctx.custom_id)
        except JSONDecodeError:
            logging.info("Interaction made with invalid persistent custom_id. Skipping.")
            return

        if callback := self._modal_callbacks.get(pid.tag):
            if callback[1] == 0:
                args = [item for item in ctx.responses]
                print(args)
                await self._modal_callbacks[pid.tag][0](ctx, pid.package, *args)
            else:
                kwargs = {item.components[0].custom_id: item.components[0].value for item in ctx.responses}
                await self._modal_callbacks[pid.tag][0](ctx, pid.package, **kwargs)
