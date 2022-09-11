from typing import Optional, Union
import random
from dataclasses import dataclass, field
from neurons.xy import XY
from neurons.fiber import Fiber
from neurons.node import Node
from typing import Union

def _random_length(rng=random):
    return rng.randint(1, 10)

@dataclass
class Nerve:
    """
    A nerve is a connected fiber. The final position of its fiber will be read
    by all the connected targets, and modified by the weights. The clock is
    used to decide when values propogate to the next element in the fiber.
    """

    unique_id: int
    is_axon: bool = False
    length: int = field(default_factory=_random_length)
    source: Optional[Union[Node, "Nerve"]] = None
    target: list[Union[Node, "Nerve"]] = field(
        default_factory=list
    )
    myelin: Fiber = None
    output: int = 0
    stimulation: int = 0
    pos: XY = field(default_factory=XY, repr=True)
    weights: list[float] = field(default_factory=list)
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

        return (
            f"Nerve(name={self.unique_id}. "
            f"{self.myelin} "
            f"targets={[t.unique_id for t in self.target]})"
        )

