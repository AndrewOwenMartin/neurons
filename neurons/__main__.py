import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import neurons

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()


def main():

    neurons.main()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
