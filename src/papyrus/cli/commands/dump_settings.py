from ._base import BaseCommand


class DumpSettingsCommand(BaseCommand):
    name = "dump_settings"
    help = "dump the current settings"

    def execute(self, agent, args) -> int:
        """dump the current settings"""
        settings = agent.settings
        print(settings.yaml())
        return 0
