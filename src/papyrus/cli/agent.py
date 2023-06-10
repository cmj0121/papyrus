"""The agent instance"""
import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from functools import cached_property

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
    env = ".env"

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
        return Settings(_env_file=self.env)

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
            case 0:
                level = logging.ERROR
            case 1:
                level = logging.WARNING
            case 2:
                level = logging.INFO
            case _:
                level = logging.DEBUG

        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)

        formatter = logging.Formatter("[%(asctime)s] %(filename)s#L%(lineno)04d - %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
