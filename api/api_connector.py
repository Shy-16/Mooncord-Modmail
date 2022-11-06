# -*- coding: utf-8 -*-
#pylint: disable=unused-variable,unused-argument,too-many-lines

import requests
import json

def do_api_call(endpoint, api_token, data=None, headers=None, method="GET"):

    if not data:
        data = dict()

    if not headers:
        headers = {
            'd-api-key': f'{api_token}',
            'content-type': 'application/json; charset=utf8'
        }

    if method == "GET":
        request = requests.get(endpoint, headers=headers, params=data, timeout=60)

    elif method == "POST":
        request = requests.post(endpoint, headers=headers, data=json.dumps(data), timeout=60)

    elif method == "PUT":
        request = requests.put(endpoint, headers=headers, data=json.dumps(data), timeout=60)

    elif method == "DELETE":
        request = requests.delete(endpoint, headers=headers, params=data, timeout=60)

    return request
