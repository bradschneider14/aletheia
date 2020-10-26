from flask.views import MethodView
from flask import Response
from flask import request
from flask import send_file

from aletheia.utils.dynamo import Dynamo
from aletheia.annotations.constants import AnnotationConstants
from aletheia.views.cors import CorsEnabledMethodView

from functools import reduce
import json
import subprocess
from tempfile import NamedTemporaryFile

import cv2

BASE_VIDEO_URL = 'https://data.bris.ac.uk/datasets/3h91syskeag572hl6tvuovwv4d/videos/train'

class BaseAnnotationView(CorsEnabledMethodView):
  def __init__(self, provider_url):
    self._provider = Dynamo(provider_url)

class AnnotationView(BaseAnnotationView):
  def get(self):
    args = {}
    # look for query parameters
    final_query = ''
    query_expr_list = [self._provider.get_query_expr('cons_verb', '', 'ne')]
    for key in request.args:
      if key == 'LIMIT':
        args['limit']=int(request.args[key])
      else:
        query_expr_list.append(self._provider.get_query_expr(key, request.args.get(key)))
        print(f'Found parameter: {key}, {request.args[key]}')
    if query_expr_list:
      final_query = reduce(self._provider.conjunctify_query, query_expr_list)
    results = self._provider.query_table(AnnotationConstants.ANNOTATION_TABLE_NAME, final_query, **args)

    return self._build_response(Response(response=json.dumps({'annotations':results}), status=200))

class AnnotationItemView(BaseAnnotationView):
  def get(self, annotation_id):
    if annotation_id:
      annotations = self._provider.query_by_id(AnnotationConstants.ANNOTATION_TABLE_NAME, AnnotationConstants.ANNOTATION_PRIMARY_KEY, annotation_id)
      if annotations:
        return self._build_response(Response(response=json.dumps({"annotations": annotations}), status=200))
      else:
        return self._build_response(Response(status=404))

  def put(self, annotation_id):
    if annotation_id:
      print(f'request JSON: {request.json}')
      update_vals = {key:val for key, val in request.json.items() if key in AnnotationConstants.ANNOTATION_OBJECT_KEYS}
      print(f'update vals: {update_vals}')
      response = self._provider.update_item(AnnotationConstants.ANNOTATION_TABLE_NAME, annotation_id, update_vals)
      print(response)
    return self._build_response(Response(response=json.dumps(response), status=200))
  
  
class AnnotationImageView(BaseAnnotationView):
  def get(self, annotation_id):
    annotations = self._provider.query_by_id(AnnotationConstants.ANNOTATION_TABLE_NAME, AnnotationConstants.ANNOTATION_PRIMARY_KEY, annotation_id)
    if annotations:
      annotation = annotations[0]

      frame_num = annotation.get('start_frame')
      seconds = float(frame_num)/60.0

      source = annotation.get('source')
      participant = source[1:4]

      temp = NamedTemporaryFile(suffix='.gif')
      print(f'Created temp file {temp.name}')

      video_url = f'{BASE_VIDEO_URL}/{participant}/{source[1:]}.MP4'

      #subprocess.call(['ffmpeg', '-ss', f'{seconds:.3f}', '-i', f'{video_url}', '-frames:v', '1', '-y', temp.name])
      subprocess.call(['ffmpeg', '-ss', f'{seconds:.3f}', '-t', '0.5', '-i', f'{video_url}', 
                       '-vf', 'fps=10,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                       '-loop', '0', '-y', temp.name])
      return self._build_response(send_file(temp, mimetype='image/gif'))
    return self._build_response(Response(response={}, status=404))


