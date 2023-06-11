from __future__ import annotations

import abc
from argparse import ArgumentParser
from argparse import Namespace


class BaseCommand(abc.ABC):
    name: str | None = None
    help: str | None = None

    _commands: dict[str, BaseCommand] = {}

    def __init_subclass__(subcls, *args, **kwargs):
        if subcls.name is None:
            raise ValueError(f"{subcls.name} must have a name")

        if subcls.name in BaseCommand._commands:
            raise ValueError(f"{subcls.name} is already registered")

        BaseCommand._commands[subcls.name] = subcls
        super().__init_subclass__(*args, **kwargs)

    @classmethod
    def commands(cls):
        return cls._commands

    @classmethod
    def get_command(cls, name: str) -> BaseCommand | None:
        return cls._commands.get(name)

    # ======== the general methods to execute command ======== #
    @classmethod
    def add_arguments(cls, parser: ArgumentParser):
        pass

    @abc.abstractmethod
    def execute(self, agent, args: Namespace) -> int:
        """should implement this method to handle the command"""
        raise NotImplementedError
