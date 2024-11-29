import tempfile

import blendersynth as bsyn
import unittest
import cv2
import numpy as np

class UnitTestCompositor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bsyn.render.set_cycles_samples(10)
        bsyn.render.set_resolution(256, 256)

        bsyn.world.set_color((0.5, 1.0, 0.5)) # Set color to test for color mapping.

        cube = bsyn.Mesh.from_primitive('cube')
        camera = bsyn.Camera()
        comp = bsyn.Compositor()

        camera.location = (0, 0, 5)
        camera.look_at_object(cube)

        normal_aov = bsyn.aov.NormalsAOV()
        cube.assign_aov(normal_aov)

        comp.define_output('Image', 'rgb', is_data=False)
        comp.define_output(normal_aov, 'normal8', is_data=True, color_depth="8")
        comp.define_output(normal_aov, 'normal16', is_data=True, color_depth="16")
        cls.render_result = comp.render()

        # Load images.
        cls.image_data = {}
        for key in ['rgb', 'normal8', 'normal16']:
            path = cls.render_result.get_render_path(key)
            cls.image_data[key] = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

    def test_normal_8_render(self):
        img = self.image_data['normal8']

        # Normal should point in camera's negative Z.
        self.assertSequenceEqual(list(img[128, 128]), [128, 128, 0])

    def test_normal_16_render(self):
        img = self.image_data['normal16']

        # Normal should point in camera's negative Z.
        self.assertSequenceEqual(list(img[128, 128]), [128, 128, 0])

    def test_rgb_render(self):
        """Test that an 'Image' render matches the colorspace of the actual output render."""
        img = self.image_data['rgb']

        # Reading Render Result fails, so must save to disk first.
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            bsyn.data.images['Render Result'].save(filepath=f.name)
            render_np = cv2.cvtColor(cv2.imread(f.name), cv2.COLOR_BGR2RGB)

        # All pixels should be the same
        np.testing.assert_allclose(img, render_np, atol=0.1)