import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import unittest

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()
# import neurons.config
# config = neurons.config.load()
import neurons.world


class TestWorld(unittest.TestCase):
    def test_world(self):

        world = neurons.world.World()

        log.info("world:\n%s", world.render())

        model = neurons.world.DummyModel(world=world)

        model.run(max_time=None)

    def setUp(self):

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        )
