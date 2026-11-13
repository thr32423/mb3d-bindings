"""python -m unittest discover -s tests   (in python/; the library: built in ../ffi, or LIBMB3D=/path/to/libmb3d.so)"""

import os
import struct
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import mb3d


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = mb3d.Engine(cpu=True)

    @classmethod
    def tearDownClass(cls):
        cls.engine.close()

    def test_a_preset_changes_and_renders(self):
        s = self.engine.preset("Integer Power")
        s.set(iterations=8, rotation=(-40, 30, 10))
        self.assertEqual(s.get("iterations"), "8")
        self.assertAlmostEqual(s.rotation[0], -40, places=4)
        with self.assertRaises(mb3d.Mb3dError):
            s.set("no_such_key = 1")
        seen = []
        p = s.render(width=96, progress=lambda stage, done, total: seen.append((stage, done, total)))
        self.assertEqual((p.width, p.height), (96, 72))
        self.assertEqual(p.png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", p.png[16:24]), (96, 72))
        self.assertEqual(s.width, 800, "the scene keeps its own size")

    def test_pixels_depth_and_files(self):
        s = self.engine.preset("Amazing Box").resize(width=64)
        p = s.render(pixels=True, depth=True)
        self.assertEqual(len(p.rgb), p.width * p.height * 3)
        self.assertEqual(len(p.depth), p.width * p.height * 2)
        self.assertTrue(any(p.depth))
        with tempfile.TemporaryDirectory() as d:
            png, m3p = os.path.join(d, "a.png"), os.path.join(d, "a.m3p")
            q = s.render(file=png)
            self.assertIsNone(q.png)
            self.assertGreater(os.path.getsize(png), 100)
            s.save(m3p)
            again = self.engine.open(m3p)
            self.assertEqual((again.width, again.height), (s.width, s.height))
            with open(m3p, "rb") as f:
                self.assertEqual(self.engine.from_bytes(f.read()).formulas, s.formulas)
        self.assertEqual(self.engine.from_text(s.text()).text(), s.text())

    def test_formulas_and_copies(self):
        self.assertIn("Amazing Box", self.engine.formulas())
        self.assertTrue(self.engine.formula_settings("Amazing Box"))
        self.assertIn("zoom", self.engine.guide())
        box = self.engine.preset("Amazing Box")
        slot = box.formula_values[0]["slot"]
        self.assertEqual(box.formula_values[0]["settings"]["Scale"], 2)
        box.set_formula(slot, {"Scale": 2.5}, iterations=2)
        self.assertEqual((box.formula_values[0]["settings"]["Scale"], box.formulas[0][1]), (2.5, 2))
        with self.assertRaises(mb3d.Mb3dError):
            box.set_formula(slot, {"No such value": 1})
        a = self.engine.preset("Integer Power")
        b = a.copy().set(zoom=2)
        self.assertNotEqual(a.get("zoom"), b.get("zoom"))
        a.close()
        with self.assertRaises(mb3d.Mb3dError):
            a.text()

    def test_a_render_is_cancelled(self):
        s = self.engine.preset("Integer Power")
        started = threading.Event()
        timer = threading.Thread(target=lambda: (started.wait(), self.engine.cancel()), daemon=True)
        timer.start()
        with self.assertRaises(mb3d.Mb3dError) as e:
            s.render(width=4000, progress=lambda *a: started.set())
        timer.join()
        self.assertEqual(str(e.exception), "cancelled")
        self.assertEqual(s.render(width=64).width, 64, "the engine goes on after a cancel")


if __name__ == "__main__":
    unittest.main()
