import logging
import os
from sekupy.analysis.base import Analyzer
from sekupy.utils.time import get_time
from sekupy.utils.files import make_dir
from collections import Counter

logger = logging.getLogger(__name__)


class AnalysisPipeline(Analyzer):
    

    def __init__(self, configurator, name="base"):
        """This class is used to perform a general analysis based on
        the configuration that is specified by the parameter.
        (see ```sekupy.analysis.configurator.Configurator``` docs)
        
        Parameters
        ----------
        configurator : ```sekupy.analysis.configurator.Configurator```
            object used to specify the preprocessing and the analysis 
            to be performed
        name : str, optional
            [description] (the default is "base")
        
        """
     
        self._configurator = configurator
        self.name = name
            

    def fit(self, ds=None, **kwargs):
        """Fit the analysis on the dataset.
        
        Parameters
        ----------
        ds : pymvpa dataset
            The dataset is the input to the analysis.

        kwargs : dict
            Optional parameters for the analysis.
        
        """
        
        objects = self._configurator.fit()

        self._loader = objects['loader']
        self._transformer = objects['transformer']
        self._estimator = objects['estimator']

        logger.debug(self._estimator)

        if (ds is None) and (self._loader is not None):
            fetch_kw = self._configurator._get_function_kwargs(function="fetch")
            logger.info(fetch_kw)
            ds = self._loader.fetch(**fetch_kw)
        elif (ds is None) and (self._loader is None):
            raise Exception("You must specify a dataset or a loader in the Configurator!")
        
        self._ds = ds
        ds_ = self._transform(ds)
        _ = self._estimator.fit(ds_, **kwargs)
        
        return self

    def _get_ds(self):
        if hasattr(self, '_ds'):
            return self._ds
        
        objects = self._configurator.fit()

        self._loader = objects['loader']
        fetch_kw = self._configurator._get_function_kwargs(function="fetch")
        logger.info(fetch_kw)
        ds = self._loader.fetch(**fetch_kw)

        return ds



    def _transform(self, ds):
        
        self._configurator._default_options['ds__target_count_pre'] = Counter(ds.targets)
        
        # TODO: Is it useful??
        ds_dict = {"ds.a.%s" % (k): v.value for k, v in ds.a.items()}
        self._configurator._default_options.update(ds_dict)

        for node in self._transformer.nodes:
            ds = node.transform(ds)
            
            if node.name in ['balancer', 'target_transformer']:
                key = 'ds__target_count_%s' % (node.name)
                self._configurator._default_options[key] = Counter(ds.targets)
        
        return ds



    def save(self, path=None, subdir="0_results", save_ds=False, **kwargs):
        # TODO: Mantain subdir for compatibility purposes?
        
        # params = self._configurator._get_fname_info()
        # params.update(self._estimator._get_fname_info())
        params = self._configurator._default_options
        
        logger.debug(params)
        
        if 'path' in kwargs.keys():
            path = kwargs.pop("path")
        
        if 'path' in params.keys():
            path = params.pop("path")

        params['pipeline'] = self.name
        params.update(kwargs)
        
        # Save results
        path = self._estimator.save(path=path, **params)

        if save_ds:
            self._save_ds(path=path)
        
        return
    
    def _save_ds(self, path):
        id_ = self._configurator._default_options['id']
        num_ = self._configurator._default_options['num']
        name_ = self.name
        fname = "ds_pipeline-%s_id-%s_num-%s.gzip" % (name_, id_, num_)
        self._ds.save(os.path.join(path, fname), compression='gzip')
    
