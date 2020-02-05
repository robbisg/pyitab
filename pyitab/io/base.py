#######################################################
#     Copyright (c) 2013 Roberto Guidotti
#
#     See the file license.txt for copying permission.
########################################################
from __future__ import print_function

import os
from mvpa2.misc.io.base import SampleAttributes
from mvpa2.datasets.mri import fmri_dataset
from mvpa2.datasets.eventrelated import eventrelated_dataset, find_events
from mvpa2.base.dataset import vstack


import logging
import numpy as np
import nibabel as ni


from pyitab.utils.files import add_subdirs, build_pathnames
from pyitab.io.subjects import add_subjectname

logger = logging.getLogger(__name__) 


def load_dataset(path, subj, folder, **kwargs):
    ''' Load a 2d dataset given the image path, the subject and the main folder of 
    the data.

    Parameters
    ----------
    path : string
       specification of filepath to load
    subj : string
        subject name (in general it specifies a subfolder under path)
    folder : string
        subfolder under subject folder (in general is the experiment name)
    kwargs : keyword arguments
        Keyword arguments to format-specific load

    Returns
    -------
    ds : ``Dataset``
       Instance of ``mvpa2.datasets.Dataset``
    '''

    roi_labels = dict()
    extract_events = False

    for arg in kwargs:
        if arg == 'roi_labels':             # dictionary of mask {'mask_label': string}
            roi_labels = kwargs[arg]
        elif arg == 'extract_events':
            extract_events = bool(kwargs[arg])
    
    
    # Load the filename list        
    file_list = load_filelist(path, subj, folder, **kwargs)   

    
    # Load data
    try:
        fmri_list = load_fmri(file_list)
    except IOError as err:
        logger.error(err)
        return
    
       
    # Loading attributes
    attr = load_attributes(path, subj, folder, **kwargs)
    
    if (attr is None) and (len(file_list) == 0):
        return None            

    # Loading mask 
    mask = load_mask(path, **kwargs)
    roi_labels['brain'] = mask
    
    # Check roi_labels
    roi_labels = load_roi_labels(roi_labels)
          
    
    # Load the pymvpa dataset.    
    try:
        logger.info('Loading dataset...')
        
        ds = fmri_dataset(fmri_list, 
                          targets=attr.targets, 
                          chunks=attr.chunks, 
                          mask=mask,
                          add_fa=roi_labels)
        
        logger.debug('Dataset loaded...')
    except ValueError as e:
        logger.error("ERROR: %s (%s)", e, subj)
        del fmri_list
    
    
    # Add filename attributes for detrending purposes   
    ds = add_filename(ds, fmri_list)
    del fmri_list
    
    # Update Dataset attributes
    if extract_events:
        ds = add_events(ds)
    
    # Name added to do leave one subject out analysis
    ds = add_subjectname(ds, subj)
    
    # If the attribute file has more fields than chunks and targets    
    ds = add_attributes(ds, attr)
         
    return ds 



def add_filename(ds, fmri_list):
    
    filenames = []
    for i, img in enumerate(fmri_list):
        for _ in range(img.shape[-1]):
            filenames.append(img.get_filename())
        
    # For each volume we store to which file it belongs to
    ds.sa['file'] = filenames

    return ds
    


def add_attributes(ds, attr):
    
    
    logger.debug(attr.keys())
    
    try:
        for k in attr.keys():
            ds.sa[k] = attr[k]
    except BaseException as err:        
        logger.error(str(err))
        
    return ds


def add_events(ds):
    
    ev_list = []
    events = find_events(targets=ds.sa.targets, chunks=ds.sa.chunks)
    for i in range(len(events)):
        duration = events[i]['duration']
        for _ in range(duration):
            ev_list.append(i + 1)
    
    ds.a['events'] = events # Update event field
    ds.sa['events_number'] = ev_list # Update event number
    
    return ds



def load_filelist(path, name, folder, **kwargs):
    ''' Load file given the filename

    Parameters
    ----------
    path : string
       specification of filepath to load
    name : string
        subject name (in general it specifies a subfolder under path)
    folder : string
        subfolder under subject folder (in general is the experiment name)
    kwargs : keyword arguments
        Keyword arguments to format-specific load

    Returns
    -------
    file_list : string list
       list of strings indicating the file pathname
    '''
    
    img_pattern='.nii.gz'
    
    for arg in kwargs:
        if (arg == 'img_pattern'):
            img_pattern = kwargs[arg] 
        if (arg == 'sub_dir'):
            sub_dirs = kwargs[arg].split(',')

    file_list = build_pathnames(path, name, sub_dirs)
  
    # Filter list
    file_list = [elem for elem in file_list 
                 if (elem.find(img_pattern) != -1)]

    logger.debug(' Matching files ')
    logger.debug(file_list)

    if file_list is not None:
        file_list.sort()
        
    return file_list
  


def load_roi_labels(roi_labels):
    
    roi_labels_dict = {}
    if roi_labels is not None:
        for label, img in roi_labels.items():
            if isinstance(img, str):
                roi_labels_dict[label] = ni.load(img)
            else:
                roi_labels_dict[label] = img
    
    logger.debug(roi_labels_dict)

    return roi_labels_dict




def load_fmri(filelist):
    """Load data specified in the file list as nibabel image.
    
    Parameters
    ----------
    filelist : list
        List of pathnames specifying the location of image to be loaded
    
    Returns
    -------
    fmri_list: 
        List of nibabel images.
    """

    image_list = []
        
    for file_ in filelist:
        
        logger.info('Now loading '+file_)     
        
        img = ni.load(file_)
        image_list.append(img)
        
        logger.debug(img.shape)
        logger.debug(img.get_filename())
    
    logger.debug('The image list is of ' + str(len(image_list)) + ' images.')
    
    return image_list



def load_mask(path, **kwargs):
    
    for arg in kwargs: 
        if (arg == 'mask_dir'):
            mask_path = kwargs[arg]
            if mask_path[0] != '/':
                mask_path = os.path.join(path, mask_path)
        if (arg == 'brain_mask'):
            rois = kwargs[arg].split(',')
                              
    mask_list = find_roi(mask_path, rois)
       
    # Load Nifti from list
    data = 0
    for m in mask_list:
        img = ni.load(os.path.join(mask_path, m))
        data = data + img.get_data() 
        logger.info('Mask used: '+img.get_filename())

    mask = ni.Nifti1Image(data.squeeze(), img.affine)
    logger.debug("Mask shape: "+str(mask.shape))
        
    return mask



def find_roi(path, roi_list):
    
    logger.debug(roi_list)
    
    found_rois = os.listdir(path)
    mask_list = []
    
    for roi in roi_list:
        mask_list += [m for m in found_rois if m.find(roi) != -1]
   
    mask_list = [m for m in mask_list if m.find(".nii.gz")!=-1 or m.find(".img")!=-1 or m.find(".nii") != -1]
    
    logger.debug(' '.join(mask_list))
    logger.info('Mask searched in '+path+' Mask(s) found: '+str(len(mask_list)))
    
    return mask_list
 
    


def load_attributes (path, subj, task,  **kwargs):
    
    # TODO: Maybe is better to use explicit variables
    # instead of kwargs

    header = ['targets', 'chunks']
    
    for arg in kwargs:
        if (arg == 'sub_dir'):
            sub_dirs = kwargs[arg].split(',')
        if (arg == 'event_file'):
            event_file = kwargs[arg]
        if (arg == 'event_header'):
            header = kwargs[arg].split(',')
            # If it's one item is a boolean
            if len(header) == 1:
                header = np.bool(header[0])
            
    
    directory_list = add_subdirs(path, subj, sub_dirs)
    
    attribute_list = []
    
    logger.debug(directory_list)
    
    for d in directory_list:
        temp_list = os.listdir(d)
        attribute_list += [os.path.join(d,f) for f in temp_list if f.find(event_file) != -1]
        
        
    logger.info(attribute_list)
    
    # Small check
    if len(attribute_list) > 2:
        attribute_list = [f for f in attribute_list if f.find(subj) != -1]
        
    
    if len(attribute_list) == 0:
        logger.error('ERROR: No attribute file found!')
        logger.error( 'Checked in '+str(directory_list))
        return None
    
    
    logger.debug(header)
    
    attr_fname = attribute_list[0]
    
    attr = SampleAttributes(attr_fname, header=header)
    return attr
