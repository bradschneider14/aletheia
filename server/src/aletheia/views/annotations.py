from flask.views import MethodView
from flask import Response
from flask import request
from flask import send_file

from aletheia.utils.dynamo import Dynamo
from aletheia.annotations.constants import AnnotationConstants

from functools import reduce
import json
import subprocess
from tempfile import NamedTemporaryFile

import cv2

BASE_VIDEO_URL = 'https://data.bris.ac.uk/datasets/3h91syskeag572hl6tvuovwv4d/videos/train'

class BaseAnnotationView(MethodView):
  def __init__(self, provider_url):
    self._provider = Dynamo(provider_url)

class AnnotationView(BaseAnnotationView):
  def get(self):  
    # look for query parameters
    final_query = ''
    query_expr_list = []
    for key in request.args:
      query_expr_list.append(self._provider.get_query_expr(key, request.args.get(key)))
      print(f'Found parameter: {key}, {request.args[key]}')
    if query_expr_list:
      final_query = reduce(self._provider.conjunctify_query, query_expr_list)
    results = self._provider.query_table(AnnotationConstants.ANNOTATION_TABLE_NAME, final_query)

    return {'annotations': results}, 200

class AnnotationItemView(BaseAnnotationView):
  def get(self, annotation_id):
    if annotation_id:
      annotations = self._provider.query_by_id(AnnotationConstants.ANNOTATION_TABLE_NAME, AnnotationConstants.ANNOTATION_PRIMARY_KEY, annotation_id)
      if annotations:
        return Response(response=json.dumps({"annotations": annotations}), status=200)
      else:
        return Response(status=404)
  
class AnnotationImageView(BaseAnnotationView):
  def get(self, annotation_id):
    annotations = self._provider.query_by_id(AnnotationConstants.ANNOTATION_TABLE_NAME, AnnotationConstants.ANNOTATION_PRIMARY_KEY, annotation_id)
    if annotations:
      annotation = annotations[0]

      frame_num = annotation.get('start_frame')
      seconds = float(frame_num)/60.0

      source = annotation.get('source')
      participant = source[1:4]

      temp = NamedTemporaryFile(suffix='.png')
      print(f'Created temp file {temp.name}')

      video_url = f'{BASE_VIDEO_URL}/{participant}/{source[1:]}.MP4'
      subprocess.call(['ffmpeg', '-ss', f'{seconds:.3f}', '-i', f'{video_url}', '-frames:v', '1', '-y', temp.name])
      return send_file(temp, mimetype='image/png')
    return {}, 404


