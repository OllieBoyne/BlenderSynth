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