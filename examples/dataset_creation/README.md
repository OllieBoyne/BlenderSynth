**Dataset creation**

Here we show an example of how to create a large scale dataset. There are three important scripts:

1) `blender_script.py` - This is the script that performs the rendering. It is called by the `create_dataset.py` script.
2) `generate_labels.py` - This script generates the per-instance labels (e.g. lighting, pose) that will be used when generating the dataset.
3) `create_dataset.py` - This script calls the `blender_script.py` script to generate the dataset, managing threading.

This is the most robust way to generate datasets. `generate_labels.py` could be managed inside `blender_script.py`, but you may run into issues of managing seeding between threads & jobs, which is why generating it outside of the script is desirable.