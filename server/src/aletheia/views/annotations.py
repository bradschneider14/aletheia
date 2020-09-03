from flask.views import MethodView
from flask import Response
import json

from aletheia.annotations.provider import AnnotationSelector

class AnnotationsView(MethodView):
  def __init__(self, provider):
    self._provider = provider

  def get(self, annotation_id):
    if annotation_id:
      selector = AnnotationSelector(annotation_id=annotation_id)
      annotations = self._provider.get_annotations(selector)

      if annotations:
        return Response(response=json.dumps({"annotations": annotations}), status=200)
      else:
        return Response(status=404)
    else:
      return "Hello!"