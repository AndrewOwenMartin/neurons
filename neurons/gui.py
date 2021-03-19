import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import neurons.model
from dearpygui import core, simple
from dearpygui.core import *
from dearpygui.simple import *

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()


def update_drawing(sender, data):
    x = get_value("circleX")
    y = get_value("circleY")
    radi = get_value("radius")
    col = get_value("color")
    modify_draw_command(
        "drawing##widget", "movingCircle", center=[x, y], radius=radi, color=col
    )


def gui_main(model):
    def show_state(sender, data):

        print(model.jsonable_state)

    def increment(sender, data):

        model.simulate(step_count=1)

    with simple.window(
        f"Main Window",
    ):

        add_drawing("drawing##widget", width=800, height=600)

        draw_circle(
            "drawing##widget",
            [100, 100],
            50,
            [0, 255, 255, 255],
            tag="bumCircle",
        )

        for node in model.nodes:

            draw_circle(
                "drawing##widget",
                [node.pos.x * 800, node.pos.y * 600],
                50,
                [0, 255, 255, 255],
                tag=f"myCircle{node.unique_id}",
            )

    with simple.window("mini window"):
        core.add_text(f"Hello world")

        core.add_button(f"Show state", callback=show_state)

        core.add_button(f"Increment", callback=increment)

    core.start_dearpygui(primary_window="Main Window")


def main():

    model = neurons.model.get_default_model()

    gui_main(model)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
