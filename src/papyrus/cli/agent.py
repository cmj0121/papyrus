"""The agent instance"""
import enum
import logging
import sys
from argparse import ArgumentParser
from argparse import Namespace
from functools import cached_property

from papyrus.settings import PROJ_NAME
from papyrus.settings import Settings
from papyrus.storage import Storage
from papyrus.types import Data
from papyrus.types import Key
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexer import RegexLexer
from pygments.token import Keyword
from pygments.token import Text

from .commands import Command

logger = logging.getLogger(PROJ_NAME)


class Action(enum.Enum):
    EXIT = "exit"
    INSERT = "insert"
    DELETE = "delete"
    LATEST = "latest"
    REVISION = "revision"
    SEARCH = "search"

    @classmethod
    def to_list(cls) -> list[str]:
        return [action.value for action in cls]


class PromptLexer(RegexLexer):
    tokens = {
        "root": [
            (r"list", Keyword),
            (r"dump_settings", Keyword),
            *[(action.value, Keyword) for action in Action],
            (r"\s+", Text.Whitespace),
            (r"[\w=]+", Text),
        ],
    }


class Agent:
    """
    The agent instance of Papyrus

    The agent is the main and only one interface of Papyrus, and the user can use the
    agent to interact with the data stored in Papyrus.
    """

    help = "the embeddable, persistent, and revision storage"
    env = ".env.yml"

    @classmethod
    def add_arguments(cls, parser: ArgumentParser):
        parser.add_argument("-c", "--config", default=cls.env, help="The path of the .env file")

        group = parser.add_mutually_exclusive_group()
        group.add_argument("-q", "--quiet", action="store_true", help="Silence the log")
        group.add_argument("-v", "--verbose", action="count", help="Show the verbose log")

        subcmd = parser.add_subparsers(dest="action")
        for name, command in Command.commands().items():
            subparser = subcmd.add_parser(name, help=command.help)
            command.add_arguments(subparser)

    @cached_property
    def settings(self) -> Settings:
        """The global settings of Papyrus"""
        with open(self.env, encoding="utf-8") as fd:
            return Settings.parse_raw(fd.read())

    @cached_property
    def storage(self) -> Storage:
        """The storage of Papyrus"""
        storage = Storage.open(self.settings.layers)
        return storage

    def _prologue(self, args: Namespace):
        """setup the necessary environment and configuration before running the agent"""
        self.env = args.config or self.env
        self._setup_logger(quiet=args.quiet, verbose=args.verbose)

    def _setup_logger(self, /, quiet: bool = False, verbose: int = 0):
        """setup the logger"""
        if quiet and verbose:
            raise ValueError("cannot set both `quiet` and `verbose`")

        if quiet:
            verbose = -1

        match verbose:
            case None:
                level = self.settings.log_level.name
                level = getattr(logging, level)
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

    @cached_property
    def session(self) -> PromptSession:
        actions = [*Command.commands().keys(), *Action.to_list()]

        session = PromptSession(
            auto_suggest=AutoSuggestFromHistory(),
            lexer=PygmentsLexer(PromptLexer),
            completer=WordCompleter(actions, ignore_case=True),
        )
        return session

    def run(self, args: Namespace) -> int:
        """The main entry of Papyrus"""
        self._prologue(args)

        if args.action is not None:
            command = Command.get_command(args.action)
            return command().execute(self, args)

        return self._run(args)

    def get_text(self) -> str:
        if sys.stdin.isatty():
            return self.session.prompt("> ")

        return input()

    def _run(self, args) -> int:
        """run the agent REPL"""

        lexer = PromptLexer()
        while True:
            try:
                text = self.get_text()
                cmd, *args = list(lexer.get_tokens(text))

                cmd = cmd[1]  # only get the command text
                cmd = Action(cmd) if cmd in Action._value2member_map_ else cmd

                if any(arg for typ, arg in args if typ not in (Text, Text.Whitespace)):
                    print(f"[!] invalid command: {text}")
                    continue

                args = [arg for typ, arg in args if typ is Text]
                match cmd:
                    case Action.EXIT:
                        break
                    case Action.INSERT:
                        match len(args):
                            case 1:
                                key, = args
                                value = None
                                tags = {}
                            case 2:
                                key, value = args
                                tags = {}
                            case _:
                                key, value, *tags = args

                                tags = [tag.split("=") for tag in tags]
                                tags = {tag[0]: Key("=".join(tag[1:])) for tag in tags}

                        self.storage.insert(Data(key, value=value, tags=tags))
                    case Action.DELETE:
                        for key in args:
                            self.storage.delete(key)
                    case Action.LATEST:
                        for key in args:
                            data = self.storage.latest(key)
                            if data is not None and not data.is_deleted and data.value is not None:
                                print(data.value)
                    case Action.REVISION:
                        for key in args:
                            revision = self.storage.revision(Key(key))
                            revision = "\n".join(map(str, revision))
                            print(revision)
                    case Action.SEARCH:
                        match len(args):
                            case 1:
                                tname, tvalue = args[0].split("=")
                                tvalue = Key(tvalue)
                            case _:
                                print(f"[!] invalid command: {text}")
                                continue

                        for key in self.storage.search(tname, tvalue):
                            print(key)
                    case _:
                        command = Command.get_command(cmd)
                        if command is None:
                            logger.error(f"unknown command: {cmd}")
                            continue

                        if command().execute(self, args) != 0:
                            logger.error(f"failed to execute command: {cmd}")
                            return 1
            except KeyboardInterrupt:
                print("Ctrl-D to exit")
                continue
            except EOFError:
                break
            except Exception as err:
                logger.critical(f"unhandled exception: {err}")
                return 1

        return 0
