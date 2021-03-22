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

    def get_delta(self, target):

        return XY(
            *(
                target_element - self_element
                for self_element, target_element in zip(self, target)
            )
        )

    def segmentize(self, target, segment_count):

        if segment_count == 1:

            return [(self, target)]

        delta = self.get_delta(target)

        segment_start = self
        segment_end = None

        for segment_num in range(1, segment_count + 1):

            segment_end = XY(
                *[
                    self_dimension + (delta_dimension * segment_num / segment_count)
                    for self_dimension, delta_dimension in zip(self, delta)
                ]
            )

            yield (segment_start, segment_end)
            segment_start = segment_end


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

    @property
    def jsonable_state(self):

        return {
            "unique_id": self.unique_id,
            "pos": list(self.pos),
            "energy": self.energy,
            "firing": int(self.firing),
            "axon": self.axon.unique_id,
            "output": self.output,
            "stimulation": self.stimulation,
        }


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
    pos: XY = dataclasses.field(default_factory=XY, repr=True)
    weights: typing.List[float] = dataclasses.field(default_factory=list)

    def __post_init__(self):

        if self.myelin is None:

            self.myelin = Fiber([0] * self.length, maxlen=self.length)

        else:

            self.length = self.myelin.maxlen

    @property
    def jsonable_state(self):

        return {
            "unique_id": self.unique_id,
            "is_axon": self.is_axon,
            "length": self.length,
            "target": [t.unique_id for t in self.target],
            "myelin": list(self.myelin),
            "output": self.output,
            "stimulation": self.stimulation,
        }

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
            # Nodes start firing if not firing and energy is high
            # Nodes stop firing if firing and energy is low
            # Then if they're firing they
            # - Set their output to 1 (or all their remaining energy)
            # - Stimulate their axon by a slightly reduces weight
            # - Reduce their energy
            # If they're not firing they
            # - Put the stimulation in to their 'energy' battery
            # - Empty their stimulation
            # - Set their output to 0
            if not node.firing and node.energy > 3:

                node.firing = True

            elif node.firing and node.energy < 1:

                node.firing = False

            if node.firing:

                node.output = min(1, node.energy)

                node.axon.stimulation += node.output

                node.energy -= node.output

            else:

                node.energy += node.stimulation

                node.stimulation = 0

                node.output = 0

    def do_nerves():

        for nerve in nerves:
            # Nerves pop their rightmost energy as output
            # Nerves push their stimulation.

            nerve.output = nerve.myelin.pop()

            nerve.myelin.appendleft(nerve.stimulation)

            nerve.stimulation = 0

            for target, weight in zip(nerve.target, nerve.weights):

                new_stim = (nerve.output * weight) / len(nerve.target)

                log.silent(
                    "%s -> %s. stim: (%.2f * %.2f)/%s = %s",
                    nerve.unique_id,
                    target.unique_id,
                    nerve.output,
                    weight,
                    len(nerve.target),
                    new_stim,
                )

                target.stimulation += new_stim

    if step_count:

        step_gen = range(step_count)

    else:

        step_gen = itertools.count(start=0)

    for step_num in step_gen:

        log.silent("\nstep %s", step_num)

        do_free_energy()

        do_firing()

        do_nerves()

        # for node in nodes:

        #    print(node)

        # for nerve in nerves:

        #    if not nerve.is_axon:

        #        print(nerve)

        # time.sleep(0.2)


class Model:
    def __init__(self):

        self.nodes = []
        self.nerves = []

        self.unique_id_gen = itertools.count()

    def add_node(self, axon_length=10, unique_id=None):

        new_nerve = self.add_nerve(length=axon_length, is_axon=True)

        if unique_id is None:

            unique_id = next(self.unique_id_gen)

        new_node = Node(
            axon=new_nerve,
            unique_id=unique_id,
        )

        # new_nerve.source = new_node

        self.nodes.append(new_node)

        return new_node

    def add_nerve(
        self, is_axon=False, source=None, target=None, length=10, unique_id=None
    ):

        if unique_id is None:

            unique_id = next(self.unique_id_gen)

        new_nerve = Nerve(
            length=length,
            unique_id=unique_id,
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

    def attach(self, source, target, weight=1):

        if isinstance(source, Node):

            source = source.axon

        source.target.append(target)
        source.weights.append(weight)
        # target.source = source

    def simulate(self, step_count=None):

        simulate(nodes=self.nodes, nerves=self.nerves, step_count=step_count)

    @property
    def jsonable_state(self):

        return {
            "nodes": [node.jsonable_state for node in self.nodes],
            "nerves": [nerve.jsonable_state for nerve in self.nerves],
        }


def get_default_model():

    model = Model()

    node_1 = model.add_node()

    nerve_2 = model.add_nerve(source=node_1, target=None)

    nerve_3 = model.add_nerve(source=nerve_2, target=None)

    node_2 = model.add_node()

    model.attach(node_1, node_2)

    model.attach(node_2, nerve_2)

    return model


def get_default_model_002():

    model = Model()

    nodes = [model.add_node(unique_id=f"node{num}") for num in range(4)]

    pos_list = [
        XY(*pos)
        for pos in [
            (0.2, 1 - 0.7),
            (0.5, 1 - 0.2),
            (0.9, 1 - 0.8),
            (0.9, 1 - 0.4),
        ]
    ]

    for node, pos in zip(nodes, pos_list):

        node.pos = pos
        node.axon.pos = pos

    nerves = [model.add_nerve(unique_id=f"nerve{num}") for num in range(4)]

    nerve_pos_list = [
        (0.5, 1 - 0.7),
        (0.5, 1 - 0.7),
        (0.99, 1 - 0.6),
        (0.8, 1 - 0.4),
    ]

    for nerve, pos in zip(nerves, nerve_pos_list):

        nerve.pos = XY(*pos)

    model.attach(nodes[0], nerves[0])
    model.attach(nodes[0], nerves[1])
    model.attach(nerves[0], nodes[2], weight=0.5)
    model.attach(nerves[1], nodes[3])
    model.attach(nodes[2], nodes[3])
    model.attach(nodes[3], nerves[2])
    model.attach(nerves[2], nodes[2])
    model.attach(nodes[3], nerves[3])
    model.attach(nerves[3], nodes[1], weight=0.1)

    return model


def main():

    model = get_default_model_002()

    simulate(model.nodes, model.nerves, step_count=None)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
