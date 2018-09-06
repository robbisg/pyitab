import numpy as np
from mvpa_itab.pipeline import Transformer
from mvpa_itab.conn.connectivity import z_fisher


import logging
logger = logging.getLogger(__name__)




class MathTransformer(Transformer):
    
    def __init__(self, name, fx, **kwargs):
        self._fx = fx
        Transformer.__init__(self, name=name, **kwargs)
        
        
    def transform(self, ds):
        
        logger.info("Transforming samples with %s" %(str(self._fx)))
        ds_ = ds.copy()
        samples = self._fx(ds_.samples)
        samples[np.isinf(samples)] = 1
        samples[np.isnan(samples)] = 0
        
        ds_.samples = samples
        
        return ds_




class ZFisherTransformer(MathTransformer):
    
    
    def __init__(self, name='zfisher', **kwargs):
        MathTransformer.__init__(self, name=name, fx=z_fisher, **kwargs)
       
    
    
    

class AbsoluteValueTransformer(MathTransformer):
    
    
    def __init__(self, name='abs', **kwargs):
        MathTransformer.__init__(self, name=name, fx=np.abs, **kwargs)
        
        
        
        
        
        