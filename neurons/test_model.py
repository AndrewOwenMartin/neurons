import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import unittest

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()
import neurons.config
import neurons.model as model
from neurons.model import XY

config = neurons.config.load()


class TestModel(unittest.TestCase):
    def setUp(self):

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        )

    def test_segmentize(self):

        a = XY(0, 0)

        b = XY(1, 1)

        segments = list(a.segmentize(b, segment_count=10))

        log.info("segments:\n%s", "\n".join(str(x) for x in segments))
