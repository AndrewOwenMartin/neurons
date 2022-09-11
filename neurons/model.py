import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import dataclasses
import numpy as np
import math
import time
import typing
from timeit import default_timer as timer
from neurons.fiber import Fiber



log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()



@dataclasses.dataclass
class FreeEnergy:
    """
    Represents some spontaneous energy in the world which can be picked up by
    nearby neurons. They have position and degrade over time.
    """

    pos: XY = dataclasses.field(default_factory=XY, repr=True)
    mag: float = 1
    drawn: bool = False


class Model:
    """
    The model represents the entire simulation, it is responsible for recording
    and updating the state of all nodes and nerves. If we move to a Brain,
    Body, World setup then it should hold all the state, and update it, but
    `nodes` and `nevers` will be wrapped up in the `Brain` class.

    Nodes and nerves must be added with `add_node` and `add_nerve`, which must
    then be connected with calls to `attach`.
    """

    free_energy_per_second = 20
    distance_decay = 2  # 2 = Inverse squared law
    distance_scale = 10  # Power of a unit distance, E.g. how far away x=0  and x=1 are
    neuron_output_per_second = 5
    nerve_propogation_time = 1
    energy_stop_firing_threshold = 1
    energy_start_firing_threshold = 5
    axon_efficiency = 1

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
                axon_efficiency=Model.axon_efficiency,
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
        axon_efficiency,
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

                node.axon.stimulation += node.output * axon_efficiency

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
