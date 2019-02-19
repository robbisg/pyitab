from pyitab.io.loader import DataLoader
from pyitab.io.base import load_dataset
from pyitab.io.connectivity import load_mat_ds
from pyitab.preprocessing.pipelines import PreprocessingPipeline
from pyitab.preprocessing.pipelines import StandardPreprocessingPipeline
import numpy as np
import os
import unittest

currdir = os.path.dirname(os.path.abspath(__file__))
currdir = os.path.abspath(os.path.join(currdir, os.pardir))

class BaseTest(unittest.TestCase):

    def setUp(self):
        self.ds = self.fetch_dataset()

    def fetch_dataset(self, task='fmri'):

        if task != 'fmri':
            reader = load_mat_ds
            prepro = PreprocessingPipeline()
        else:
            reader = load_dataset
            prepro = StandardPreprocessingPipeline()

        datadir = os.path.join(currdir, 'io', 'data', task)
        configuration_file = os.path.join(datadir, '%s.conf' %(task))

        loader = DataLoader(configuration_file=configuration_file, 
                            task=task,
                            loader=reader)

        ds = loader.fetch(prepro=prepro)

        return ds


if __name__ == '__main__':
    unittest.main()