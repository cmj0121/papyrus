"""The agent instance"""
import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from functools import cached_property

from papyrus.layers import Layer
from papyrus.settings import PROJ_NAME
from papyrus.settings import Settings

from .commands import Command

logger = logging.getLogger(PROJ_NAME)


class Agent:
    """
    The agent instance of Papyrus

    The agent is the main and only one interface of Papyrus, and the user can use the
    agent to interact with the data stored in Papyrus.
    """

    help = "the embeddable, persistent, and revisions storage"
    env = ".env.yml"

    @classmethod
    def add_arguments(cls, parser: ArgumentParser):
        parser.add_argument("-c", "--config", default=cls.env, help="The path of the .env file")

        group = parser.add_mutually_exclusive_group()
        group.add_argument("-q", "--quiet", action="store_true", help="Silence the log")
        group.add_argument("-v", "--verbose", default=0, action="count", help="Show the verbose log")

        subcmd = parser.add_subparsers(dest="action", required=True)
        for name, command in Command.commands().items():
            subparser = subcmd.add_parser(name, help=command.help)
            command.add_arguments(subparser)

    @cached_property
    def settings(self) -> Settings:
        """The global settings of Papyrus"""
        with open(self.env, encoding="utf-8") as fd:
            return Settings.parse_raw(fd.read())

    @cached_property
    def layers(self) -> list[Layer]:
        """The layers of Papyrus"""
        return [Layer.open(name) for name in self.settings.LAYERS]

    def run(self, args: Namespace) -> int:
        """The main entry of Papyrus"""
        self._prologue(args)

        command = Command.get_command(args.action)
        return command().execute(self, args)

    def _prologue(self, args: Namespace):
        """setup the necessary environment and configuration before running the agent"""
        self._setup_logger(quiet=args.quiet, verbose=args.verbose)

    def _setup_logger(self, /, quiet: bool = False, verbose: int = 0):
        """setup the logger"""
        if quiet and verbose:
            raise ValueError("cannot set both `quiet` and `verbose`")

        if quiet:
            verbose = -1

        match verbose:
            case -1:
                level = logging.CRITICAL
                self.settings.log_level = "critical"
            case 0:
                level = logging.ERROR
                self.settings.log_level = "error"
            case 1:
                level = logging.WARNING
                self.settings.log_level = "warning"
            case 2:
                level = logging.INFO
                self.settings.log_level = "info"
            case _:
                level = logging.DEBUG
                self.settings.log_level = "debug"

        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)

        formatter = logging.Formatter("[%(asctime)s] %(filename)s#L%(lineno)04d - %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
