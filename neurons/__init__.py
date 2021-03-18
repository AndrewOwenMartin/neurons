import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import dataclasses
import numpy as np
import math
import time
import typing


log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()


@dataclasses.dataclass
class XY:

    x: float = dataclasses.field(default_factory=rng.random)
    y: float = dataclasses.field(default_factory=rng.random)

    def __repr__(self):

        return f"XY({self.x:3.2f}, {self.y:3.2f})"

    def distance(a, b):

        return math.sqrt(sum((a_elem - b_elem) ** 2 for a_elem, b_elem in zip(a, b)))

    def __iter__(self):

        yield self.x
        yield self.y


@dataclasses.dataclass
class Node:

    index: int
    pos: XY = dataclasses.field(default_factory=XY, repr=True)
    energy: float = 0
    firing: bool = False

    def __repr__(self):

        return f"Node(pos={self.pos}, energy={self.energy:3.2f}, firing={self.firing})"


@dataclasses.dataclass
class Nerve:

    length: int = dataclasses.field(default_factory=lambda: rng.randint(1, 10))
    source: typing.Optional[Node] = None
    target: typing.Optional[Node] = None
    myelin: typing.Deque[float] = None

    def __post_init__(self):

        if self.myelin is None:

            self.myelin = collections.deque([0] * self.length, maxlen=self.length)

        else:

            self.length = self.myelin.maxlen

    def __repr__(self):

        return (
            f"Nerve({self.source.index} -> {list(self.myelin)} -> {self.target.index})"
        )


@dataclasses.dataclass
class FreeEnergy:

    pos: XY = dataclasses.field(default_factory=XY, repr=True)
    mag: float = 1


def simulate(nodes, nerves, step_count=None):

    free_energy_per_tick = 1
    distance_decay = 2
    distance_scale = 10

    def decay(distance):

        dropoff = 1 / pow((distance * distance_scale) + 1, distance_decay)

        log.silent("dropoff for distance %.3f is %.3f", distance, dropoff)

        return dropoff

    def do_free_energy():

        free_energy_count = np.random.poisson(free_energy_per_tick, 1)[0]

        free_energy_gen = (FreeEnergy() for num in range(free_energy_count))

        for free_energy in free_energy_gen:

            for node in nodes:

                distance = XY.distance(node.pos, free_energy.pos)

                node.energy += free_energy.mag * decay(distance)

    def do_firing():

        for node in nodes:

            if node.firing:

                node.energy *= 0.8

                if node.energy < 1:

                    node.firing = False

            else:

                if node.energy > 5:

                    node.firing = True

    if step_count:

        step_gen = range(step_count)

    else:

        step_gen = itertools.count(start=0)

    for step_num in step_gen:

        log.info("\nstep %s", step_num)

        do_free_energy()

        do_firing()

        for node in nodes:

            print(node)

        time.sleep(0.2)


def main():

    node_count = 10

    nodes = [Node(index=x) for x in range(node_count)]

    nerve_count = node_count

    in2nerve = collections.defaultdict(list)
    out2nerve = collections.defaultdict(list)
    nerves = []

    for (source, target) in sorted(
        rng.sample(list(itertools.permutations(range(node_count), 2)), nerve_count)
    ):

        nerve = Nerve(3, nodes[source], nodes[target])

        in2nerve[source].append(nerve)
        out2nerve[target].append(nerve)

        nerves.append(nerve)

    for nerve in nerves:

        print(nerve)

    simulate(nodes, nerves, step_count=2)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
