# -*- coding: utf-8 -*-
"""Smoke tests for Acoustica app startup."""

import unittest

from src.app import AcousticaApp


class TestAcousticaAppStartup(unittest.TestCase):
    def test_app_initializes(self):
        app = AcousticaApp()
        self.assertIsNotNone(app)
        self.assertIsNotNone(app._state)
        self.assertGreater(app._state.width, 0)


if __name__ == "__main__":
    unittest.main()
