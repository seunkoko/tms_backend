from flask import request, jsonify, json, Response
from flask_restful import Resource

from ...auth.token import token_required


class RouteResource(Resource):
    
    @token_required
    def get(self):
        return {
            'status': 'success',
            'data': { 'message': "successfully created the route resource" }
        }, 200
