import collections, datetime, functools, itertools
import json, logging, pathlib, random, re
import neurons.model
import neurons.config

config = neurons.config.load()

import dearpygui.core as core
import dearpygui.simple as simple

log = logging.getLogger(__name__)
log.silent = functools.partial(log.log, 0)

rng = random.Random()

nerve_off_color = config["colors"].getColor("nerve off")
nerve_on_color = config["colors"].getColor("nerve on")
node_off_color = config["colors"].getColor("node off")
node_firing_color = config["colors"].getColor("node firing")
node_charging_color = config["colors"].getColor("node charging")


def interpolate_color(start, end, factor):

    return [int(s + factor * (e + s)) for s, e in zip(start, end)]


def draw_nerve(nerve, target_pos, window_scale, tag):

    segment_gen = nerve.pos.segmentize(target_pos, nerve.length)

    for segment_num, (start_pos, target_pos) in enumerate(segment_gen):

        core.draw_line(
            drawing="drawing##widget",
            p1=window_scale(start_pos),
            p2=window_scale(target_pos),
            color=nerve_off_color,
            thickness=1,
            tag=f"{tag}-segment-{segment_num:03}",
        )


def scale(vec, dim):

    return [x * y for x, y in zip(vec, dim)]


def render(model, window_scale, dim):

    # for num, free_energy in enumerate(model.free_energies):

    #    #core.modify_draw_command(
    #    #    "drawing##widget",
    #    #    f"freeEnergy{num}",
    #    #    center=window_scale(free_energy.pos),
    #    #    radius=min(dim) * 0.1 * free_energy.mag,
    #    #)

    #    log.info("draw free energy#%s", num)
    for num, free_energy in enumerate(model.free_energies):

        if free_energy is None:

            continue

        tag = f"freeEnergy{num}"

        if free_energy.mag < 0 and free_energy.drawn:

            log.info("deleting %s", tag)

            core.delete_draw_command("drawing##widget", tag)

        else:

            if free_energy.drawn:

                core.modify_draw_command(
                    "drawing##widget",
                    tag,
                    # center=window_scale(free_energy.pos),
                    radius=20 * free_energy.mag,
                )

            else:

                core.draw_circle(
                    "drawing##widget",
                    center=window_scale(free_energy.pos),
                    # radius=min(dim) * 0.1 * free_energy.mag,
                    radius=20 * max(0, 1 / free_energy.mag),
                    color=[255, 0, 0],
                    fill=[255, 0, 0],
                    tag=tag,
                )

                free_energy.drawn = True

    for node in model.nodes:

        energy = node.energy / model.energy_start_firing_threshold

        if node.firing:

            node_color = interpolate_color(node_off_color, node_firing_color, energy)

        else:

            node_color = interpolate_color(node_off_color, node_charging_color, energy)

        tag = f"myCircle{node.unique_id}"

        core.modify_draw_command(
            "drawing##widget",
            tag,
            fill=node_color,
        )

    for nerve in model.nerves:

        for target in nerve.target:

            for segment_num, energy in enumerate(nerve.myelin):

                nerve_color = interpolate_color(
                    nerve_off_color, nerve_on_color, energy / 5
                )

                core.modify_draw_command(
                    "drawing##widget",
                    f"nerve-from-{nerve.unique_id}-to-{target.unique_id}-segment-{segment_num:03}",
                    color=nerve_color,
                )


def gui_main(model):

    dim = (800, 600)

    window_scale = functools.partial(scale, dim=dim)

    def show_state(sender, data):

        print(model.jsonable_state)

    def show_free_energies(sender, data):

        print(
            [(num, fe) for num, fe in enumerate(model.free_energies) if fe is not None]
        )

    def show_neurons(sender, data):

        model_state = model.jsonable_state

        node_dicts = [
            {
                "name": node["unique_id"],
                "firing": node["firing"],
                "energy": format(node["energy"], "0.2f"),
            }
            for node in model_state["nodes"]
        ]

        print("\n".join(str(x) for x in node_dicts))

    def increment(sender, data):

        print("increment does not work, put in a 1s alternative")

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

        for num, free_energy in enumerate(model.free_energies):

            if free_energy is None:

                continue

            core.draw_circle(
                "drawing##widget",
                window_scale(free_energy.pos),
                min(dim) * 0.1 * free_energy.mag,
                color=[255, 0, 0],
                fill=[255, 0, 0],
                tag=f"freeEnergy{num}",
            )

            log.info("drawing fe")

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

    with simple.window("Controls", x_pos=350, y_pos=230, height=120):
        core.add_text(f"Interact with the model.")

        core.add_button(f"Log state", callback=show_state)

        core.add_button(f"Log neurons", callback=show_neurons)

        core.add_button(f"Step model", callback=increment)

        core.add_button(f"Show free energies", callback=show_free_energies)

    def my_render():

        dt = core.get_delta_time()

        model.advance(dt=dt)

        render(model, window_scale, dim)

    core.set_render_callback(my_render)
    core.set_vsync(True)

    core.start_dearpygui(primary_window="Main Window")


def main():

    model = neurons.model.get_default_model_003()

    for node in model.nodes:

        node.energy = rng.uniform(0, model.energy_start_firing_threshold)

    gui_main(model)


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="%(asctime)s %(levelname)-4s %(name)s %(message)s",
        style="%",
    )

    main()
