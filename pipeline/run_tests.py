from __future__ import absolute_import

import os
import unittest

import crater_pipeline


class TestGeneralFunctionality(unittest.TestCase):

    def test_case1(self):
        """Just a temporary test for project setup purposes.
        """

        dataholder = crater_pipeline.DataHolder("maya", "win32")
        result = dataholder.sum_list([2, 2])
        expected_result = 4

        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
