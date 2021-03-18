import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
from importlib import reload
import neurons.config
#import pandas as pd
#import numpy as np
#import plotnine as p9

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

config = neurons.config.load()

rng = random.Random()

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )
