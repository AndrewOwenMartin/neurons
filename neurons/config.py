import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import configparser
import functools
import pathlib
import pkg_resources

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()

config_file_paths = (
    pkg_resources.resource_filename(__name__, "neurons.conf"),
    pathlib.Path("~").expanduser() / "config" / "neurons.conf",
)


def load():

    config_parser = configparser.ConfigParser(
        converters={
            "Color": lambda s: json.loads(s),
        }
    )

    for config_file_path in config_file_paths:

        config_file_path = pathlib.Path(config_file_path)

        if config_file_path.exists():

            log.info("loading config from %s", config_file_path)

            config_parser.read(config_file_path)

    return config_parser
