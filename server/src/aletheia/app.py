import argparse
import json
import os

from aletheia.annotations.provider import HDFProvider
from aletheia.annotations.provider import DataSource
from aletheia.annotations.provider import AnnotationSelector

from aletheia.views.annotations import AnnotationsView

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
    self._flask.add_url_rule('/annotation/<annotation_id>', view_func=AnnotationsView.as_view('annotations', self._annotation_provider))
    #self._flask.add_url_rule('/annotation/<annotation_id>/image', view_func=AnnotationsView.as_view('annotations_image', self._annotation_provider))

  def run(self, host:str, port:int)->None:
    print('Starting server...')
    self._flask.run(host=host, port=port)




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

  port = os.environ.get('PORT', 8000)
  app.run('0.0.0.0', port)

  
