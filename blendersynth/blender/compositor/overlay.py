"""Add an overlay to an image."""

import cv2
from .render_result import RenderResult
import tempfile
from pathlib import Path
import numpy as np

class Overlay:

    def __init__(self, keys_in: list[str], key_out: str):
        self.keys_in = keys_in
        self.key_out = key_out

    def apply(self, render_result:RenderResult):
        """keys_in: All input keys to load from render_result
        key_out: Key to save as in render_result"""

        for camera in render_result.camera_names:
            for frame in render_result.frames:
                print(self.keys_in, render_result.render_paths)
                paths_in = [render_result.get_render_path(key, camera, frame) for key in self.keys_in]
                path_out = self.run(paths_in)
                render_result.add(self.key_out, camera, frame, path_out, overwrite=True)

    def run(self, paths_in) -> Path:
        """paths_in: List of paths to input images.
        Returns: Path to output image."""
        raise NotImplementedError

class BackgroundColor(Overlay):

    def __init__(self, keys_in: list[str], key_out: str, background_color: tuple):
        super().__init__(keys_in, key_out)
        self.background_color = background_color

    def run(self, paths_in):
        render_path, alpha_path = paths_in
        render = cv2.cvtColor(cv2.imread(render_path), cv2.COLOR_BGR2RGB)
        alpha = (cv2.imread(alpha_path, cv2.IMREAD_GRAYSCALE) / 255.0)[:, :, None]

        background_color_image = np.full(render.shape, self.background_color) * 255
        render = background_color_image * (1 - alpha) + render * alpha
        render = render.astype(np.uint8)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            cv2.imwrite(f.name, cv2.cvtColor(render, cv2.COLOR_RGB2BGR))
            return Path(f.name)