import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
from importlib import reload
import neurons
import neurons.config
try:
    import pandas as pd
except ModuleNotFoundError:
    pass
try:
    import numpy as np
except ModuleNotFoundError:
    pass
try:
    import plotnine as p9
except ModuleNotFoundError:
    pass

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

config = neurons.config.load()
