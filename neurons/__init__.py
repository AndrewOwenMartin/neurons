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


class Fiber(collections.deque):

    str_template = "[{x}]"

    def __str__(self):

        return Fiber.str_template.format(
            x=", ".join(format(x, ".2f") if x > 0 else " .  " for x in self)
        )


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

    unique_id: int
    pos: XY = dataclasses.field(default_factory=XY, repr=True)
    energy: float = 0
    firing: bool = False
    axon: typing.Optional["Nerve"] = None
    output: int = 0
    stimulation: int = 0

    def __repr__(self):

        return f"Node(id={self.unique_id} pos={self.pos}, energy={self.energy:3.2f}, firing={int(self.firing)}, axon={self.axon.myelin} -> {[target.unique_id for target in self.axon.target]})"

    def __lt__(self, other):

        return self.unique_id < other.unique_id


@dataclasses.dataclass
class Nerve:

    unique_id: int
    is_axon: bool = False
    length: int = dataclasses.field(default_factory=lambda: rng.randint(1, 10))
    source: typing.Optional[typing.Union[Node, "Nerve"]] = None
    target: typing.List[typing.Union[Node, "Nerve"]] = dataclasses.field(
        default_factory=list
    )
    myelin: Fiber = None
    output: int = 0
    stimulation: int = 0

    def __post_init__(self):

        if self.myelin is None:

            self.myelin = Fiber([0] * self.length, maxlen=self.length)

        else:

            self.length = self.myelin.maxlen

    def __repr__(self):

        return f"Nerve(name={self.unique_id}. {self.myelin} targets={[t.unique_id for t in self.target]})"


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
            # Nodes put the stimulation in to their 'energy' battery
            # Then if they're firing they
            # - Set their output to 1 (or all their remaining energy)
            # - Reduce their energy
            # - Stop firing if energy is low
            # If they're not firing they
            # - Set their output to 0
            # - Start firing if energy is high

            node.energy += node.stimulation

            node.stimulation = 0

            if node.firing:

                node.output = min(1, node.energy)

                node.axon.stimulation += node.output * 0.5

                node.energy -= node.output

                if node.energy < 1:

                    node.firing = False

            else:

                node.output = 0

                if node.energy > 3:

                    node.firing = True

    def do_nerves():

        for nerve in nerves:
            # Nerves pop their rightmost energy as output
            # Nerves push their stimulation.

            nerve.output = nerve.myelin.pop()

            nerve.myelin.appendleft(nerve.stimulation)

            nerve.stimulation = 0

            for target in nerve.target:

                target.stimulation += nerve.output / len(nerve.target)

    if step_count:

        step_gen = range(step_count)

    else:

        step_gen = itertools.count(start=0)

    for step_num in step_gen:

        log.info("\nstep %s", step_num)

        do_free_energy()

        do_firing()

        do_nerves()

        for node in nodes:

            print(node)

        for nerve in nerves:

            if not nerve.is_axon:

                print(nerve)

        time.sleep(0.2)


class Model:
    def __init__(self):

        self.nodes = []
        self.nerves = []

        self.unique_id_gen = itertools.count()

    def add_node(self, axon_length=10):

        new_nerve = self.add_nerve(length=axon_length, is_axon=True)

        new_node = Node(
            axon=new_nerve,
            unique_id=next(self.unique_id_gen),
        )

        # new_nerve.source = new_node

        self.nodes.append(new_node)

        return new_node

    def add_nerve(self, is_axon=False, source=None, target=None, length=10):

        new_nerve = Nerve(
            length=length,
            unique_id=next(self.unique_id_gen),
            is_axon=is_axon,
        )

        if source is not None:

            if isinstance(source, Nerve):

                source.target.append(new_nerve)
                # new_nerve.source = source

            elif isinstance(source, Node):

                source.axon.target.append(new_nerve)
                # new_nerve.source = source.axon

        if target is not None:

            if isinstance(target, (Nerve, Node)):

                new_nerve.target.append(target)

            else:

                for item in target:

                    new_nerve.target.append(item)

        self.nerves.append(new_nerve)

        return new_nerve

    def attach(self, source, target):

        if isinstance(source, Node):

            source = source.axon

        source.target.append(target)
        # target.source = source

    def simulate(self, step_count=None):

        simulate(nodes=self.nodes, nerves=self.nerves, step_count=step_count)


def main():

    nodes = []
    nerves = []

    model = Model()

    node_1 = model.add_node()

    nerve_2 = model.add_nerve(source=node_1, target=None)

    nerve_3 = model.add_nerve(source=nerve_2, target=None)

    node_2 = model.add_node()

    model.attach(node_1, node_2)

    model.attach(node_2, nerve_2)

    simulate(model.nodes, model.nerves, step_count=None)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
