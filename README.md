# BlenderSynth

![](docs/splash.png)

Synthetic Blender pipeline - aimed at generating large synthetic datasets.

BlenderProc is an incredibly useful tool for synthetic dataset generation. We aim here to provide an alternative that is (a) more specialised for uncommon data forms, and (b) runs faster for creating large scale datasets.

We produce support for:
- Custom Shader AOVs (eg. UVs, Normals, etc.)
- Multi-threading support
- Efficient run-speed

## Installation

1) Install [Blender](https://www.blender.org)

2) Install blendersynth

First, blendersynth needs to be able to find your Blender installation. There are many ways to do this:
- Add Blender to PATH (so that `blender` can be called from the command line)
- Set the `BLENDER_PATH` environment variable to the path to your Blender installation
- Pass the `--blender_path` argument to `python setup.py install`
- If none of these are done, you will be prompted to give the location of your Blender installation during install

From pip:

```pip install blendersynth```

Or:

`python setup.py install [--blender_path /path/to/blender]`

## Quickstart

For a quick overview of creating a render: `examples/quickstart.py`

For an overview of creating a dataset: `examples/dataset_creation`

## Contributions

This project is currently in Beta. Please let me know what new features you would like, or feel free to make a pull request!
For a list of actions, see [].

Note that `bsyn` imports all `bpy` functionality, so you can call any `bpy` function as if you would normally.

## Troubleshooting

If any issues with the Blender scripts not having the correct modules,

```python
import blendersynth as bsyn
bsyn.fix_blender_install()
```

## Benchmarking

We show significant speed improvements over BlenderProc
