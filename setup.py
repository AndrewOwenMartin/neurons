from setuptools import setup

setup(
    name="neurons",
    version="0.1",
    packages=[
        "neurons",
    ],
    description="",
    keywords=[],
    entry_points={
        "console_scripts": [
            "neurons-gui = neurons.gui:gui_main",
        ],
    },
    install_requires=[],
    classifiers=[],
    author="Andrew Owen Martin",
    author_email="andrew@aomartin.co.uk",
)
