from ._base import BaseCommand


class DumpSettingsCommand(BaseCommand):
    name = "dump_settings"
    help = "dump the current settings"

    def execute(self, agent, args) -> int:
        for key, field in agent.settings.__fields__.items():
            comment = field.field_info.description

            if comment:
                print(f"# {comment}")
                print(f"{key}={getattr(agent.settings, key)}  # [default: {field.default}]")
                print()
            else:
                print(f"{key}={getattr(agent.settings, key)}  # [default: {field.default}]")

        return 0
