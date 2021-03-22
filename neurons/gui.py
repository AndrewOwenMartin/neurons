import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import neurons.model

# from dearpygui import core, simple
import dearpygui.core as core
import dearpygui.simple as simple

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()

node_firing_fill = [255, 0, 0, 255]
node_not_firing_fill = [0, 128, 128, 255]


def draw_nerve(nerve, target_pos, window_scale, tag):

    nerve_color = [0, 255, 255, 255]

    segment_gen = nerve.pos.segmentize(target_pos, nerve.length)

    for segment_num, (start_pos, target_pos) in enumerate(segment_gen):

        log.silent("drawing nerve segment %s-%03s", tag, segment_num)

        foo = bool(rng.randint(0, 1))

        if foo:

            nerve_color = node_firing_fill

        else:

            nerve_color = node_not_firing_fill

        core.draw_line(
            drawing="drawing##widget",
            p1=window_scale(start_pos),
            p2=window_scale(target_pos),
            color=nerve_color,
            thickness=1,
            tag=f"{tag}-segment-{segment_num:03}",
        )


def scale(vec, dim):

    return [x * y for x, y in zip(vec, dim)]


def render(model):

    # print("rendering")

    for node in model.nodes:

        energy = node.energy * 0.33

        if node.firing:

            node_color = [255 * energy, 0, 0, 255]

        else:

            col = 255 * energy

            node_color = [col, col, 0, 255]

        core.modify_draw_command(
            "drawing##widget",
            f"myCircle{node.unique_id}",
            fill=node_color,
        )

    for nerve in model.nerves:

        for target in nerve.target:

            for segment_num, segment in enumerate(nerve.myelin):

                nerve_color = [255, 255 * segment, 255, 255]

                core.modify_draw_command(
                    "drawing##widget",
                    f"nerve-from-{nerve.unique_id}-to-{target.unique_id}-segment-{segment_num:03}",
                    color=nerve_color,
                )


def gui_main(model):
    def show_state(sender, data):

        model.nodes[0].energy += 3

        print(model.jsonable_state)

    def increment(sender, data):

        model.simulate(step_count=1)

        render(model)

    dim = (800, 600)

    window_scale = functools.partial(scale, dim=dim)

    # window_size = [int(x) for x in scale(dim, (1.1, 1.1))]

    # core.set_main_window_size(*(int(x for x in scale(dim, (1.1, 1.1)))))
    # core.set_main_window_size(*window_size)
    core.set_main_window_size(820, 620)

    with simple.window(
        f"Main Window",
        width=dim[0],
        height=dim[1],
    ):

        core.add_drawing("drawing##widget", width=dim[0], height=dim[1])

        core.draw_rectangle(
            "drawing##widget",
            pmin=[0, 0],
            pmax=list(dim),
            color=[255, 255, 255, 255],
        )

        for nerve in model.nerves:

            for target in nerve.target:

                draw_nerve(
                    nerve,
                    target.pos,
                    window_scale,
                    tag=f"nerve-from-{nerve.unique_id}-to-{target.unique_id}",
                )

        for node in model.nodes:

            core.draw_circle(
                "drawing##widget",
                window_scale(node.pos),
                min(dim) * 0.05,
                color=[0, 255, 255, 255],
                fill=[0, 128, 128, 255],
                tag=f"myCircle{node.unique_id}",
            )

    with simple.window("Controls"):
        core.add_text(f"Interact with the model.")

        core.add_button(f"Log state", callback=show_state)

        core.add_button(f"Step model", callback=increment)

    def my_render():

        model.simulate(step_count=1)

        render(model)

    core.set_render_callback(my_render)
    core.set_vsync(True)

    core.start_dearpygui(primary_window="Main Window")


def main():

    model = neurons.model.get_default_model_002()

    gui_main(model)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
