from flask.views import MethodView

class AnnotationsView(MethodView):
  def __init__(self, provider):
    self._provider = provider

  def get(self):
    return "Hello Annotations!"
