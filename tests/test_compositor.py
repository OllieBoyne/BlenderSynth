
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

        comp.define_output(normal_aov, 'normal', is_data=True)
        render_result = comp.render()

        path = render_result.get_render_path('normal')
        img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

        from matplotlib import pyplot as plt
        plt.imshow(img)
        plt.show()

        # Normal should point in camera's negative Z.
        self.assertSequenceEqual(list(img[128, 128]), [127, 127, 0])