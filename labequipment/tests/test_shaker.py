from unittest import TestCase
from labequipment import shaker


class TestShaker(TestCase):
    def test_start_shaker(self):
        myshaker = shaker.Shaker()
        myshaker.quit()
        self.assertTrue(True)