from typing import Optional
from neurona.xy import XY
from dataclasses import dataclass

@dataclass
class Node:
    """
    A node is the meeting place of many nerves, with a single output nerve. It
    accumulates energe and then spends some time 'firing' that energy down its
    neuron.
    
    Firing is actually just setting an output value, and any connected fiber
    will read that value.
    """

    unique_id: int
    pos: XY = dataclasses.field(default_factory=XY, repr=True)
    energy: float = 0
    firing: bool = False
    axon: Optional["Nerve"] = None
    output: int = 0
    stimulation: int = 0

    def __repr__(self):

        return (
            f"Node(id={self.unique_id} "
            f"pos={self.pos} "
            f"energy={self.energy:3.2f} "
            f"firing={int(self.firing)} "
            f"axon={self.axon.myelin} -> {[target.unique_id for target in self.axon.target]})"
        )

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
