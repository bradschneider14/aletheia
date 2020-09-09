import argparse
import json
import os

from aletheia.annotations.provider import HDFProvider
from aletheia.annotations.provider import DataSource
from aletheia.annotations.provider import AnnotationSelector

from aletheia.views.annotations import AnnotationView
from aletheia.views.annotations import AnnotationItemView
from aletheia.views.annotations import AnnotationImageView

from flask import Flask

class ServerApp:
  def __init__(self, name:str, config):
    '''
    Construct a new instance of the Server

    :param name: the name assigned to the underlying Flask instance
    :param config: an object of the following form:
        {
          "annotation_sources":[
            {
              "name":"P04_01", 
              "location":"path/to/datasource.h5"
            }
          ],
          "annotation_url": "http://localhost:8000"
        }
    '''
    self._annotation_provider = HDFProvider()
    self._flask = Flask(name)

    ann_url = config.get("annotation_url")
    if ann_url:
      self._annotation_url = ann_url

    self._create_rules()    
    
  def _create_rules(self)->None:
    self._flask.add_url_rule('/annotation', view_func=AnnotationView.as_view('annotations', self._annotation_url))
    self._flask.add_url_rule('/annotation/<annotation_id>', view_func=AnnotationItemView.as_view('annotations_item', self._annotation_url))
    self._flask.add_url_rule('/annotation/<annotation_id>/image', view_func=AnnotationImageView.as_view('annotations_image', self._annotation_url))

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

  app = ServerApp('Aletheia Server', config)

  port = os.environ.get('PORT', 5000)
  app.run('0.0.0.0', port)

  
