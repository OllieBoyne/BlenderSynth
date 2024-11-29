import os.path
from shutil import copyfile

class RenderResult:
    """Result of any form of render.

    Treated as a series of paths to the output files. Handles different output types, cameras, and frame counts.
    """

    def __init__(self, render_paths: dict[tuple, str]):
        """Expects dictionary of:

        (output_key, camera_name, frame_number) -> Path.
        """

        self._render_paths = render_paths

        self._output_types = list(set([k[0] for k in render_paths.keys()]))
        self._camera_names = list(set([k[1] for k in render_paths.keys()]))
        self._frames = list(set([k[2] for k in render_paths.keys()]))

    @property
    def output_types(self) -> list[str]:
        """List of output types."""
        return self._output_types

    @property
    def camera_names(self) -> list[str]:
        """List of camera names."""
        return self._camera_names

    @property
    def frames(self) -> list[int]:
        """List of frame numbers."""
        return self._frames

    @property
    def num_cameras(self) -> int:
        """Number of cameras in the render."""
        return len(self.camera_names)

    @property
    def num_frames(self) -> int:
        """Number of frames in the render."""
        return len(self.frames)

    @property
    def num_output_types(self) -> int:
        """Number of output types in the render."""
        return len(self.output_types)

    def get_render_path(self, output_type: str, camera_name: str = None, frame_number: int = None) -> str:
        """Get the path to a specific render output.

        :param output_type: Type of output - `name` returned from :meth:`~blendersynth.blender.compositor.compositor.Compositor.define_output`.
        :param camera_name: Name of camera to get render for. Only required if multiple cameras used.
        :param frame_number: Frame number to get render for. Only required if multiple frames used.

        :return: Path to the render output.
        """

        if camera_name is None:
            if self.num_cameras != 1:
                raise ValueError("Must specify camera name if more than one camera. Cameras: ", self.camera_names)

            camera_name = self.camera_names[0]

        if frame_number is None:
            if self.num_frames != 1:
                raise ValueError("Must specify frame number if more than one frame. Frames: ", self.frames)

            frame_number = self.frames[0]

        return self._render_paths[(output_type, camera_name, frame_number)]

    def save_all(self, output_directory: str, suppress_camera_name: bool = True, suppress_frame_number: bool = True):
        """Save all the files to a directory.

        By default, saves files in format {data_type}_{camera_name}_{frame_number}.{ext}.

        :param output_directory: Directory to save files to.
        :param suppress_camera_name: If True, suppress camera name in filename (only works if single camera).
        :param suppress_frame_number: If True, suppress frame number in filename (only works if single frame).
        """

        os.makedirs(output_directory, exist_ok=True)

        suppress_camera_name = suppress_camera_name and self.num_cameras == 1
        suppress_frame_number = suppress_frame_number and self.num_frames == 1

        for (data_type, camera, frame), path in self._render_paths.items():

            fname = f'{data_type}'
            if not suppress_camera_name:
                fname += f'_{camera}'
            if not suppress_frame_number:
                fname += f'_{frame:06d}'

            fname += os.path.splitext(path)[1]

            copyfile(path, os.path.join(output_directory, fname))

    def save_file(self, output_path: str, output_type: str, camera_name: str = None, frame_number: int = None):
        """Save a single file to a path.

        :param output_path: Path to save file to.
        :param output_type: Type of output - `name` returned from :meth:`~blendersynth.blender.compositor.compositor.Compositor.define_output`.
        :param camera_name: Name of camera to get render for. Only required if multiple cameras used.
        :param frame_number: Frame number to get render for. Only required if multiple frames used."""

        if os.path.dirname(output_path):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

        path = self.get_render_path(output_type, camera_name, frame_number)

        target_ext = os.path.splitext(output_path)[1]
        rendered_ext = os.path.splitext(path)[1]
        if target_ext != rendered_ext:
            raise ValueError(f"Output path must have same extension as rendered path. Got {target_ext}, expected {rendered_ext}.")

        copyfile(path, output_path)
