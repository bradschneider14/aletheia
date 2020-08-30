import argparse
import json

from aletheia.annotations.provider import HDFProvider
from aletheia.annotations.provider import DataSource
from aletheia.annotations.provider import AnnotationSelector

from flask import Flask

class ServerApp:
  def __init__(self, name:str):
    '''
    Construct a new instance of the Server

    :param name: the name assigned to the underlying Flask instance
    '''
    self._annotation_provider = HDFProvider()
    self._flask = Flask(name)
    self._create_rules()

  def initialize(self, config:dict)->None:
    '''
    Initializes the application from a configuration, including loading data sources.

    :param config: an object of the following form:
        {
          "annotation_sources":[
            {
              "name":"P04_01", 
              "location":"path/to/datasource.h5"
            }
          ]
        }
    '''
    for annotation in config.get("annotation_sources", []):
      print(f'Adding annotation {annotation}')
      self._annotation_provider.add_source(DataSource(annotation['location'], annotation['name']))
    
  def _create_rules(self)->None:
    self._flask.add_url_rule('/session/', view_func=SessionsView.as_view('sessions'))
    self._flask.add_url_rule('/session/<session_id>/file/', view_func=SessionFileView.as_view('session_files'))
    self._flask.add_url_rule('/session/<session_id>/file/<file_id>', view_func=IterationsView.as_view('file_iterations'))



if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run the Aletheia Annotation Server')
  parser.add_argument('-config', '--cfg', dest='config_loc', type=str, help='the path to a configuration file', required=True)

  args = parser.parse_args()

  # load the configuration
  config = {}
  with open(args.config_loc) as config_file:
    config = json.load(config_file)
  print(f'Loaded configuration: \n{config}')

  app = ServerApp('Aletheia Server')
  app.initialize(config)

  
