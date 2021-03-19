from dearpygui import core, simple
from dearpygui.core import *
from dearpygui.simple import *


def save_callback(sender, data):
    print("Save Clicked")


def gui_main():

    for num in range(3):

        with simple.window(f"Example Window {num:03}"):
            core.add_text(f"Hello world {num:03}")
            core.add_button(f"Save {num:03}", callback=save_callback)
            core.add_input_text(f"string {num:03}")
            core.add_slider_float(f"float {num:03}")

    with node_editor("Node Editor"):

        with node("Node 1"):

            with node_attribute("Node A1"):
                add_input_float("F1", width=150)

            with node_attribute("Node A2", output=True):
                add_input_float("F2", width=150)

        with node("Node 2##demo"):

            with node_attribute("Node A3"):
                add_input_float("F3", width=200)

            with node_attribute("Node A4", output=True):
                add_input_float("F4", width=200)

    core.start_dearpygui()
