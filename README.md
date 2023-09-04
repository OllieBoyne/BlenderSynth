# BlenderSynth

![](docs/splash.png)

[Documentation](https://ollieboyne.github.io/BlenderSynth/) | [GitHub](https://github.com/OllieBoyne/BlenderSynth)

Synthetic Blender pipeline - aimed at generating large synthetic datasets.

This library contains a collection of features for generating synthetic datasets. Compared to other tools, BlenderSynth is (a) more specialised for uncommon data formats, and (b) is designed for generating large scale datasets quickly and efficiently.

BlenderSynth provides support for:
- Custom Shader [AOVs](https://docs.blender.org/manual/en/latest/render/shader_nodes/output/aov.html) (eg. UVs, Normals, etc.)
- Fine-grained node control
- Multi-threading
- Efficient run-speed

## Usage

See documentation for [installation](https://ollieboyne.github.io/BlenderSynth/getting_started/installation.html) and [examples](https://ollieboyne.github.io/BlenderSynth/).

## Contributions and Projects

This project is currently in Beta. Please let me know what new features you would like, or feel free to make a pull request!

If you use BlenderSynth for a project, please [contact me](https://ollieboyne.github.io) about it - I might include it in the documentation as a usage example!

## Citing

If you use BlenderSynth in your work, please cite:

```
@software{blendersynth,
  author       = {Ollie Boyne},
  title        = {BlenderSynth},
  year         = 2023,
  publisher    = {GitHub},
  url          = {https://ollieboyne.github.io/BlenderSynth},
}
```

## Benchmarking

Rendering speed compared to [BlenderProc](https://github.com/DLR-RM/BlenderProc):

![](docs/benchmark-1.png)
