# BlenderSynth

![](docs/splash.png)

Synthetic Blender pipeline - aimed at generating large synthetic datasets.

BlenderProc is an incredibly useful tool for synthetic dataset generation. We aim here to provide an alternative that is (a) more specialised for uncommon data forms, and (b) runs faster for creating large scale datasets.

We produce support for:
- Custom Shader AOVs (eg. UVs, Normals, etc.)
- Multi-threading support
- Efficient run-speed

## Installation

1) Install Blender
2) `python setup.py install <--blender_path /path/to/blender>`
- If Blender is in PATH, you can omit the `--blender_path` argument

## Quickstart

For a quick overview of creating a render: `examples/quickstart.py`

For an overview of creating a dataset: `examples/dataset_creation`

## Contributions

This project is currently in Beta. Please let me know what new features you would like, or feel free to make a pull request!
For a list of actions, see [].

Note that `bsyn` imports all `bpy` functionality, so you can call any `bpy` function as if you would normally.

## Benchmarking

We show significant speed improvements over BlenderProc
