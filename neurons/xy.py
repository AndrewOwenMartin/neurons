import dataclasses
import random
import math

Line = Tuple[XY, XY]

@dataclasses.dataclass
class XY:
    """
    The XY is a 2D point
    """

    x: float = dataclasses.field(default_factory=random.random)
    y: float = dataclasses.field(default_factory=random.random)

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

    def segmentize(self, target, segment_count) -> Iterable[Line]:

        if segment_count == 1:

            return [(self, target)]

        delta = self.get_delta(target)

        segment_start: XY = self
        segment_end: Optional[XY] = None

        for segment_num in range(1, segment_count + 1):

            segment_end = XY(
                *[
                    self_dimension + (delta_dimension * segment_num / segment_count)
                    for self_dimension, delta_dimension in zip(self, delta)
                ]
            )

            yield (segment_start, segment_end)
            segment_start = segment_end

