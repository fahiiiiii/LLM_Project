from django.test import TestCase

class BasicTest(TestCase):
    def test_basic(self):
        self.assertEqual(1,1)