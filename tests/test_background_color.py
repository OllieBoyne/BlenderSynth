import tempfile

import blendersynth as bsyn
import unittest
import cv2
import numpy as np

class UnitTestBackgroundColor(unittest.TestCase):

    def test_background_color(self):
        bsyn.render.set_cycles_samples(10)
        bsyn.render.set_resolution(256, 256)

        comp = bsyn.Compositor(background_color=(1.0, 0.0, 0.0))

        comp.define_output('Image', 'rgb', is_data=False)
        self.render_result = comp.render()

        # Load images.
        path = self.render_result.get_render_path('rgb')
        img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

        expected_img = np.full((256, 256, 3), (255, 0, 0), dtype=np.uint8)
        np.testing.assert_array_almost_equal(img / 255, expected_img / 255, decimal=2)