import unittest
from utils import *
from parser import Parser


class TestParser(unittest.TestCase):
    def setUp(self):
        self.data = load_dataset()
        self.parser = Parser()
        self.maxDiff = None

    def test_data_exists(self):
        self.assertIsNotNone(self.data)

    def test_law_parser(self):
        for example in self.data:
            self.assertDictEqual(example["target"],
                             self.parser.parse(example["example"]))
        print("{} examples correct".format(len(self.data)))


if __name__ == '__main__':
    unittest.main()
