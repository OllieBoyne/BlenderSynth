# BlenderSynth

![](docs/splash.png)

[Documentation](https://ollieboyne.github.io/BlenderSynth/) | 

Synthetic Blender pipeline - aimed at generating large synthetic datasets.

[BlenderProc](https://github.com/DLR-RM/BlenderProc) is an incredibly useful tool for synthetic dataset generation. We aim here to provide an alternative that is (a) more specialised for uncommon data forms, and (b) runs faster for creating large scale datasets.

We produce support for:
- Custom Shader [AOVs](https://docs.blender.org/manual/en/latest/render/shader_nodes/output/aov.html) (eg. UVs, Normals, etc.)
- Fine-grained node control
- Multi-threading
- Efficient run-speed

## Installation

1) Install [Blender](https://www.blender.org)

2) Install blendersynth

If Blender is not in your PATH, you will need to specify the path to your Blender installation on install.

From pip:

```
pip install blendersynth
python -c "import blendersynth"
```

Or from local clone:

```
git clone https://github.com/OllieBoyne/BlenderSynth
cd BlenderSynth
pip install .
python -c "import blendersynth" --local
```

## Examples

[See here](https://github.com/OllieBoyne/BlenderSynth/tree/main/examples) for usage examples.

Note that `bsyn` imports all `bpy` functionality, so you can call any `bpy` function as if you would normally.

## Contributions

This project is currently in Beta. Please let me know what new features you would like, or feel free to make a pull request!


## Troubleshooting

If any issues with the Blender scripts not having the correct modules, try `bsyn.fix_blender_modules()`, or to completely reconfigure Blender, `bsyn.fix_blender_install()`. If installing from local clone, use `local=True` argument to both. If you are making changes to the local clone, use `editable=True` to install in editable mode.

## Benchmarking

![](docs/benchmark-1.png)
