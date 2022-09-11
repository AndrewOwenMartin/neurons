import collections

class Fiber(collections.deque):
    """
    The Fiber is just a list of activities, it is represented as a deque, but
    the `maxlen` parameter is no longer optional. It has no position.
    """

    str_template = "[{x}]"

    def __init__(self, iterable, maxlen):
        super().__init__(iterable, maxlen)

    def __str__(self):

        return Fiber.str_template.format(
            x=", ".join(format(x, ".2f") if x > 0 else " .  " for x in self)
        )

