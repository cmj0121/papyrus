import argparse

from papyrus.agent import Agent
from papyrus.settings import PROJ_NAME


def main() -> int:
    parser = argparse.ArgumentParser(prog=PROJ_NAME, description=Agent.help)

    Agent.add_arguments(parser)

    args = parser.parse_args()

    agent = Agent()
    return agent.run(args)
