from ._base import BaseCommand


class ListCommand(BaseCommand):
    name = "list"
    help = "list all commands"

    def execute(self, agent, args) -> int:
        """list all commands"""
        max_cmd_len = max(len(name) for name in self._commands.keys())

        print("[sub commands]")
        for name, command in self._commands.items():
            print(f"    {name:{max_cmd_len+4}s} {command.help or ''}")

        return 0
