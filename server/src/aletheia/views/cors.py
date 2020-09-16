from flask.views import MethodView
from flask import make_response

class CorsEnabledMethodView(MethodView):
  def _build_cors_preflight(self):
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    return response

  def options(self, **kwargs):
    return self._build_cors_preflight()

  def _build_response(self, response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
