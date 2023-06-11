import argparse

from papyrus.settings import PROJ_NAME

from .agent import Agent


def main() -> int:
    parser = argparse.ArgumentParser(prog=PROJ_NAME, description=Agent.help)

    Agent.add_arguments(parser)

    args = parser.parse_args()

    agent = Agent()
    return agent.run(args)
