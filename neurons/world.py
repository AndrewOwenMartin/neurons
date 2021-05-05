import collections, datetime, functools, itertools, os
import json, logging, pathlib, random, re
import time
from neurons.model import Nerve
import math

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()


class World:

    friction = 0.9

    def __init__(self, size=100, target_pos=None):

        self.size = size
        self.agents = [
            Agent(
                pos=rng.randrange(self.size),
                contact_sensor=Nerve(unique_id=1, length=1),
                position_sensor=Nerve(unique_id=2, length=1),
                motor=Nerve(unique_id=3, length=1),
                target_sensor=Nerve(unique_id=4, length=1),
                icon=icon,
            )
            for icon in "ABC"
        ]
        self.target_pos = rng.randrange(self.size)

    def render(self):

        char_buffer = ["_"] * self.size

        for agent in self.agents:

            char_buffer[math.floor(agent.pos)] = agent.icon

        return "".join(char_buffer)

    def update(self, dt):

        for agent in self.agents:

            self.update_inputs(agent=agent, dt=dt)

        for agent in self.agents:

            self.update_state(agent=agent, dt=dt)

    def update_inputs(self, agent, dt):

        other_agents = (
            other_agent for other_agent in self.agents if other_agent is not agent
        )

        if any(
            abs(agent.pos - other_agent.pos) < Agent.contact_radius
            for other_agent in other_agents
        ):

            agent.contact_sensor.output = Agent.contact_constant * dt

        agent.position_sensor.output = agent.pos * dt

        agent.target_sensor.output = abs(agent.pos - self.target_pos)

    def update_state(self, agent, dt):

        agent.vel += agent.accel
        agent.vel = agent.vel - (agent.vel * World.friction * dt)
        agent.pos = (agent.pos + agent.vel) % self.size
        agent.accel = agent.motor.output


class Agent:

    contact_radius = 2
    contact_constant = 1

    def __init__(
        self,
        pos,
        contact_sensor=None,
        position_sensor=None,
        motor=None,
        target_sensor=None,
        icon="A",
    ):

        self.accel = 0
        self.vel = 0
        self.pos = pos
        self.contact_sensor = contact_sensor
        self.position_sensor = position_sensor
        self.motor = motor
        self.target_sensor = target_sensor
        self.icon = icon

    def info(self):

        return f"{self.icon}(motor={self.motor.output:+0.2f})"


class DummyModel:
    def __init__(self, world):

        self.world = world
        self.run_time = 0
        self.accelerations = [
            dict(
                accel=rng.choice([-1, 0, 1]),
                duration=rng.uniform(1, 5),
                agent=agent,
            )
            for agent in self.world.agents
        ]

    def tick(self):

        os.system("clear")

        log.info(
            "time: %5.1f. world=%s agents=%s %s",
            self.run_time,
            self.world.render(),
            " ".join(agent.info() for agent in self.world.agents),
            " ".join(
                f"[agent={acc['agent'].icon} acc={acc['accel']:+d} dur={acc['duration']:0.2f}]"
                for acc in self.accelerations
            ),
        )

        sleep_time = rng.uniform(0.1, 0.2)

        for accel in self.accelerations:

            if accel["duration"] <= 0:

                accel["duration"] = rng.uniform(1, 5)
                accel["accel"] = rng.choice([-1, 0, 1])

            accel["agent"].motor.output = accel["accel"] * sleep_time
            accel["duration"] -= sleep_time

        time.sleep(sleep_time)

        self.world.update(dt=sleep_time)

        self.run_time += sleep_time

    def run(self, max_time):

        self.run_time = 0

        while True:

            self.tick()

            if max_time is not None and self.run_time > max_time:

                break

        log.info("finished. Time %s", self.run_time)


def main():

    log.info("__name__: %s.", __name__)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
