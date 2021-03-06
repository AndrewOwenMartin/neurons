import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import dataclasses
import numpy as np
import math
import time
import typing
from timeit import default_timer as timer


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
    clock: float = 0

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
    drawn: bool = False


class Model:

    free_energy_per_second = 20
    distance_decay = 2  # 2 = Inverse squared law
    distance_scale = 10  # Power of a unit distance, E.g. how far away x=0  and x=1 are
    neuron_output_per_second = 5
    nerve_propogation_time = 1
    energy_stop_firing_threshold = 1
    energy_start_firing_threshold = 5
    axon_inefficiency = 1

    def __init__(self):

        self.nodes = []
        self.nerves = []
        self.free_energies = [None] * Model.free_energy_per_second * 2

        self.unique_id_gen = itertools.count()

        self.advance = functools.partial(
            Model.generic_advance,
            advance_free_energy=functools.partial(
                Model.generic_advance_free_energy,
                nodes=self.nodes,
                free_energies=self.free_energies,
                free_energy_per_second=Model.free_energy_per_second,
                get_decay=functools.partial(
                    Model.generic_get_decay,
                    distance_scale=Model.distance_scale,
                    distance_decay=Model.distance_decay,
                ),
            ),
            advance_nodes=functools.partial(
                Model.generic_advance_nodes,
                nodes=self.nodes,
                energy_start_firing_threshold=Model.energy_start_firing_threshold,
                energy_stop_firing_threshold=Model.energy_stop_firing_threshold,
                neuron_output_per_second=Model.neuron_output_per_second,
                axon_inefficiency=Model.axon_inefficiency,
            ),
            advance_nerves=functools.partial(
                Model.generic_advance_nerves,
                nerves=self.nerves,
                nerve_propogation_time=Model.nerve_propogation_time,
            ),
        )

    def add_node(self, axon_length=10, unique_id=None, pos=None):

        new_nerve = self.add_nerve(length=axon_length, is_axon=True, pos=pos)

        if unique_id is None:

            unique_id = next(self.unique_id_gen)

        new_node = Node(
            axon=new_nerve,
            unique_id=unique_id,
        )

        if pos:

            new_node.pos = pos

        # new_nerve.source = new_node

        self.nodes.append(new_node)

        return new_node

    def add_nerve(
        self,
        is_axon=False,
        source=None,
        target=None,
        length=10,
        unique_id=None,
        pos=None,
    ):

        if unique_id is None:

            unique_id = next(self.unique_id_gen)

        new_nerve = Nerve(
            length=length,
            unique_id=unique_id,
            is_axon=is_axon,
        )

        if pos:

            new_nerve.pos = pos

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

    def generic_get_decay(distance, distance_scale, distance_decay):

        dropoff = 1 / pow((distance * distance_scale) + 1, distance_decay)

        return dropoff

    def generic_advance_free_energy(
        dt, nodes, free_energies, free_energy_per_second, get_decay
    ):
        def get_dead_indices(free_energies, dt):

            for num, free_energy in enumerate(free_energies):

                if free_energy is None or free_energy.mag < 0:
                    # if free_energy is None:

                    yield num

                if free_energy is not None:

                    free_energy.mag -= dt

                    log.info("fe now %s", free_energy.mag)

        dead_indices = list(get_dead_indices(free_energies, dt))

        free_energy_count = np.random.poisson(free_energy_per_second * dt, 1)[0]

        for new_free_energy_num, free_index in zip(
            range(free_energy_count), dead_indices
        ):

            new_free_energy = FreeEnergy()

            free_energies[free_index] = new_free_energy

            pos = new_free_energy.pos

            mag = new_free_energy.mag

            for node in nodes:

                distance = XY.distance(node.pos, pos)

                node.energy += mag * get_decay(distance)

    def generic_advance_nodes(
        dt,
        nodes,
        energy_start_firing_threshold,
        energy_stop_firing_threshold,
        neuron_output_per_second,
        axon_inefficiency,
    ):

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
            if not node.firing and node.energy > energy_start_firing_threshold:

                node.firing = True

            elif node.firing and node.energy < energy_stop_firing_threshold:

                node.firing = False

            if node.firing:

                node.output = min(neuron_output_per_second * dt, node.energy)

                node.axon.stimulation += node.output * axon_inefficiency

                # log.info("node axon stim: %s (dt=%s)", node.axon.stimulation, dt)

                node.energy -= node.output

            else:

                node.energy = max(0, node.energy + node.stimulation)

                node.output = 0

            node.stimulation = 0

    def generic_advance_nerves(dt, nerves, nerve_propogation_time):

        for nerve in nerves:

            if nerve.clock > nerve_propogation_time:

                # Once per second
                # Nerves pop their rightmost energy as output
                # Nerves push their stimulation.
                nerve.output = nerve.myelin.pop()

                nerve.myelin.appendleft(0)

                nerve.clock -= nerve_propogation_time

                for target, weight in zip(nerve.target, nerve.weights):

                    new_stim = (nerve.output * weight) / len(nerve.target)

                    target.stimulation += new_stim

            else:

                nerve.output = 0

            # Every tick
            # Stimulate the leftmost cell
            # Reset stimulation
            nerve.myelin[0] += nerve.stimulation

            nerve.stimulation = 0

            nerve.clock += dt

    @property
    def jsonable_state(self):

        return {
            "nodes": [node.jsonable_state for node in self.nodes],
            "nerves": [nerve.jsonable_state for nerve in self.nerves],
        }

    def generic_advance(dt, advance_free_energy, advance_nodes, advance_nerves):

        advance_free_energy(dt)
        advance_nodes(dt)
        advance_nerves(dt)


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

    pos_list = [
        XY(*pos)
        for pos in [
            (0.2, 1 - 0.7),
            (0.5, 1 - 0.2),
            (0.9, 1 - 0.8),
            (0.9, 1 - 0.4),
            (0.3, 1 - 0.5),
        ]
    ]

    nodes = [model.add_node(unique_id=f"node{num}") for num in range(len(pos_list))]

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
    model.attach(nodes[4], nodes[0])
    model.attach(nodes[1], nodes[4])

    return model


def get_default_model_003():

    obj_defs = {
        "0": ("node", XY(0.25, 0.2), [("1", 1)]),
        "1": ("node", XY(0.75, 0.2), [("3", 1)]),
        "2": ("node", XY(0.25, 0.6), [("n0", 1)]),
        "3": ("node", XY(0.75, 0.6), [("4", 1)]),
        "4": ("node", XY(0.25, 0.85), [("n1", 1)]),
        "5": ("node", XY(0.75, 0.85), [("n2", 1)]),
        "n0": ("nerve", XY(0.5, 0.25), [("0", 1), ("1", 1)]),
        "n1": ("nerve", XY(0.5, 0.75), [("5", -1)]),
        "n2": ("nerve", XY(0.5, 0.95), [("4", -1)]),
    }

    name2obj = {}

    model = Model()

    for obj_name, (obj_type, pos, targets) in obj_defs.items():

        adder = model.add_node if obj_type == "node" else model.add_nerve

        obj = adder(unique_id=obj_name, pos=pos)

        name2obj[obj_name] = obj

    for obj_name, (obj_type, pos, targets) in obj_defs.items():

        origin_obj = name2obj[obj_name]

        for target_name, weight in targets:

            target_obj = name2obj[target_name]

            model.attach(origin_obj, target_obj, weight=weight)

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
