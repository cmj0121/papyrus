import logging
import os
import select
import subprocess
import time
from pathlib import Path

from behave import given
from behave import then
from behave import when
from faker import Faker
from papyrus.types import Data
from papyrus.types import Key

logger = logging.getLogger("bdd")


class PapyrusInstance:
    def __init__(self, conf):
        command = ["papyrus", "-c", str(conf)]

        self._proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        os.set_blocking(self.proc.stdout.fileno(), False)

        self._poll = select.poll()
        self._poll.register(self.proc.stdout, select.POLLIN)

        logger.info(f"start the papyrus instance with {conf=}")

    @property
    def proc(self) -> subprocess.Popen:
        return self._proc

    def send(self, cmd: str):
        logger.info(f"execute command: {cmd}")

        self.proc.stdin.write(f"{cmd}\n".encode())
        self.proc.stdin.flush()

    def recv(self, timeout=0.7) -> str:
        lines = []
        start = time.monotonic_ns()

        timeout_ns = int(timeout * 1000000000)
        while True:
            active = self._poll.poll(0)
            if active:
                while True:
                    line = self.proc.stdout.readline()

                    if line:
                        line = line[:-1].decode()
                        lines.append(line)

                    if time.monotonic_ns() - start > timeout_ns:
                        break

            if time.monotonic_ns() - start > timeout_ns:
                break

        return "\n".join(lines)


@given("load the papyrus settings")
def step_load_papyrus_settings(context):
    context.settings = Path(__file__).parent.parent / "files/basic.yml"


@given("generate the random data as {name}")
@given("generate the random data as {name} with {amount} amount")
@given("generate the random data as {name} with {amount} amount and tag {tname}={tvalue}")
def step_generate_random_data(
    context,
    name,
    amount: str | None = None,
    tname: str | None = None,
    tvalue: str | None = None,
):
    fake = Faker()
    amount = int(amount or 1)

    tags = {}
    if tname and tvalue:
        tags[tname] = Key(tvalue)

    setattr(context, name, [Data(fake.pyint(), fake.pystr(), tags=tags) for _ in range(amount)])


@when("load the papyrus instance")
def step_load_papyrus_instance(context):
    context.proc = PapyrusInstance(context.settings)


@when("insert data {name} to the papyrus instance")
def step_insert_data(context, name):
    for data in getattr(context, name):
        tags = " ".join([f"{k}={v}" for k, v in data.tags.items()])
        context.proc.send(f"insert {data.primary_key} {data.value} {tags}")


@when("delete key from data {name} on the papyrus instance")
def step_delete_key_from_data(context, name):
    for data in getattr(context, name):
        context.proc.send(f"delete {data.primary_key}")


@then("the papyrus instance should be loaded")
def step_check_papyrus_instance(context):
    context.proc.send("list")
    resp = context.proc.recv()

    assert "sub commands" in resp
    assert "list" in resp
    assert len(resp.split("\n")) > 2


@then("the data {name} {should_be} exists in the papyrus instance")
def test_check_data_exists(context, name, should_be):
    assert should_be in ("should be", "should not be"), should_be
    should_be = should_be == "should be"

    for data in getattr(context, name):
        context.proc.send(f"latest {data.primary_key}")
        resp = context.proc.recv()

        assert data.value == resp if should_be else data.value != resp


@then("the data {name} {should_be} within the revision in the papyrus instance")
def test_check_data_within_revision(context, name, should_be):
    assert should_be in ("should be", "should not be"), should_be
    should_be = should_be == "should be"

    for data in getattr(context, name):
        context.proc.send(f"revision {data.primary_key}")
        resp = context.proc.recv()

        assert f"[+] {data.value}" in resp.split("\n") if should_be else f"[+] {data.value}" not in resp.split("\n")


@then("search tag {tname}={tvalue} and the data {name} primary key {should_be} belongs to the result")
def test_check_primary_key_belongs_to_search_result(context, name, tname, tvalue, should_be):
    assert should_be in ("should be", "should not be"), should_be
    should_be = should_be == "should be"

    for data in getattr(context, name):
        context.proc.send(f"search {tname}={tvalue}")
        resp = context.proc.recv()

        assert str(data.primary_key) in resp.split("\n") if should_be else str(data.primary_key) not in resp.split("\n")
