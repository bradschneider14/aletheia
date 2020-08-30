import pandas
from typing import List
import tempfile
import uuid

class AnnotationSelector:
  def __init__(self, annotation_id:str=None, video_id:str=None, frame_id:str=None):
    self.annotation_id = annotation_id
    self.video_id = video_id
    self.frame_id = frame_id

class DataSource:
  def __init__(self, source_path:str, source_id:str):
    self.source_path = source_path
    self.source_id = source_id

class HDFProvider:
  def __init__(self, sources:List[DataSource]=None):
    '''
    Loads the provided data store for retrieving annotations
    '''
    # mkstemp returns (file, filename)
    self._annotation_store = pandas.HDFStore(tempfile.mkstemp()[1])

    if sources:
      for source in sources:
        self.add_source(source)

  def add_source(self, source:DataSource)->None:
    '''
    Add a source of annotations (e.g. another HDF5 file)
    '''
    source_store = pandas.HDFStore(source.source_path)
    # merge object annotations with optical flow
    df = pandas.merge(source_store.get('0'),
                      source_store.get('2'),
                      on='id')
    # merge object flow
    df = pandas.merge(df,
                      source_store.get('1'),
                      left_on='obj_flow_start_frame',
                      right_on='frame_flow_start_frame')
    # merge color histogram
    df = pandas.merge(df,
                      source_store.get('3'),
                      on='id')
    # merge hand position
    df = pandas.merge(df,
                      source_store.get('4'),
                      on='id')
    self._annotation_store.put(source.source_id, df)
  

  def get_annotation(self, annotation_selector:AnnotationSelector)->pandas.Series:
    '''
    Retrieves all annotations that match the selector's properties
    '''
    df_key = annotation_selector.video_id
    if df_key:
      df_to_query = None
      results = pandas.Series()

      if f'/{df_key}' in self._annotation_store.keys():
        df_to_query = self._annotation_store.get(annotation_selector.video_id)
      
      if df_to_query is not None:
        results = df_to_query
        if annotation_selector.annotation_id:

          results = results[results['id'] == uuid.UUID(annotation_selector.annotation_id)]
        if annotation_selector.frame_id:
          results = results[results['frame_id'] == annotation_selector.frame_id]

    else:
      results = None
      for key in self._annotation_store.keys():
        df_to_query = self._annotation_store.get(key)

        sub_results = df_to_query
        if annotation_selector.annotation_id:
          sub_results = sub_results[sub_results['id'] == uuid.UUID(annotation_selector.annotation_id)]
        if annotation_selector.frame_id:
          sub_results = sub_results[sub_results['frame_id'] == annotation_selector.frame_id]

        if results is not None:
          results = results.append(sub_results)
        else:
          results = sub_results

    return results