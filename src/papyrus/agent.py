"""The agent instance"""
import enum
import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from functools import cached_property

from papyrus.settings import PROJ_NAME
from papyrus.settings import Settings

logger = logging.getLogger(PROJ_NAME)


class Action(enum.Enum):
    LIST = "list"
    SETTINGS = "settings"

    def __str__(self):
        return self.value

    @classmethod
    def to_list(cls) -> list[str]:
        return [str(action) for action in cls]


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

        parser.add_argument("action", type=Action, choices=Action, help="The action to perform")

    @cached_property
    def settings(self) -> Settings:
        """The global settings of Papyrus"""
        return Settings(_env_file=self.env)

    def run(self, args: Namespace) -> int:
        """The main entry of Papyrus"""
        self._prologue(args)

        match args.action:
            case Action.LIST:
                # dump all the actions
                print("\n".join(Action.to_list()))
            case Action.SETTINGS:
                for key, field in self.settings.__fields__.items():
                    comment = field.field_info.description

                    if comment:
                        print(f"# {comment}")
                        print(f"{key}={getattr(self.settings, key)}  # [default: {field.default}]")
                        print()
                    else:
                        print(f"{key}={getattr(self.settings, key)}  # [default: {field.default}]")
            case _:
                logger.critical(f"the action `{args.action}` is not implemented")
                return 1

        return 0

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
