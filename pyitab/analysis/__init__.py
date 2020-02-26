
def run_analysis(ds, default_config, default_options=dict(), 
                    name='mvpa', subdir="0_results", kind='combination'):
    """[summary]
    
    Parameters
    ----------
    ds : [type]
        [description]
    default_config : [type]
        [description]
    default_options : [type]
        [description]
    name : [type]
        [description]
    subdir : str, optional
        [description] (the default is "0_results", which [default_description])

    kind : str
        Indicates the type of datum given to options field.
        (values must be 'combination', 'list' or 'configuration')
        if 'combination' all possible combination of items in options will be performed
        as a cartesian product of lists.
        if 'list', elements of dictionary lists must have the same length
        if 'configuration' the elements are single configuration to be used
        'combination' or 'list' or 'configurations'
        see ```pyitab.analysis.iterator.AnalysisIterator``` documentation.

    Returns
    -------
    errs : list
        Returns the list of errors with the configuration that caused the error.
    
    """
    from pyitab.analysis.configurator import AnalysisConfigurator
    from pyitab.analysis.iterator import AnalysisIterator
    from pyitab.analysis.pipeline import AnalysisPipeline

    iterator = AnalysisIterator(default_options, 
                                AnalysisConfigurator(**default_config),
                                kind=kind
                                )

    errs = []

    for conf in iterator:
        kwargs = conf._get_kwargs()
        try:
            a = AnalysisPipeline(conf, name=name).fit(ds, **kwargs)
            a.save(subdir=subdir)
        except Exception as err:
            errs.append([conf._default_options, err])

    return errs
