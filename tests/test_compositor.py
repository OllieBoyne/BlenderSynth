
import blendersynth as bsyn
import unittest
import cv2

class UnitTestCompositor(unittest.TestCase):

    def test_normal_render(self):

        bsyn.render.set_cycles_samples(10)
        bsyn.render.set_resolution(256, 256)

        cube = bsyn.Mesh.from_primitive('cube')
        camera = bsyn.Camera()
        comp = bsyn.Compositor()

        camera.location = (0, 0, 5)
        camera.look_at_object(cube)

        normal_aov = bsyn.aov.NormalsAOV()
        cube.assign_aov(normal_aov)

        comp.define_output(normal_aov, 'normal8', is_data=True, color_depth="8")
        comp.define_output(normal_aov, 'normal16', is_data=True, color_depth="16")
        render_result = comp.render()

        path_8 = render_result.get_render_path('normal8')
        img_8 = cv2.cvtColor(cv2.imread(path_8), cv2.COLOR_BGR2RGB)

        path_16 = render_result.get_render_path('normal16')
        img_16 = cv2.cvtColor(cv2.imread(path_16), cv2.COLOR_BGR2RGB)

        # Normal should point in camera's negative Z.
        self.assertSequenceEqual(list(img_8[128, 128]), [128, 128, 0])
        self.assertSequenceEqual(list(img_16[128, 128]), [128, 128, 0])