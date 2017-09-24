#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

__author__ = 'Florents Tselai'

import csv
from urllib.parse import urlencode

import redis
from flask import Flask, jsonify, request, send_file

from .config import REDIS_URI, SEARCH_BASE_URL
from .parser import parse_car_page, parse_search_results

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

redis_con = redis.StrictRedis(REDIS_URI, decode_responses=True)


@app.route("/api/car/<car>", methods=["GET"])
def get_car(car):
    return jsonify(parse_car_page(car))


@app.route("/api/search", methods=["GET"])
def search():
    request_args = request.args.to_dict()

    new_request_args=[]
    for a in request_args:
        list=request.args.getlist(a)
        for b in list:
            new_request_args.append((a,b))

    # check if format is specified and remove it
    export_format = request_args.pop('format', 'json')

    # pass the rest as search params
    search_url = SEARCH_BASE_URL + '?' + urlencode(new_request_args)

    results = parse_search_results(search_url, redis_con)

    if export_format == 'json':
        return jsonify(results)

    elif export_format == 'csv':
        with open(app.root_path + 'data.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            for d in results:
                # images is a list - not suitable for csv
                d.pop('images')
                writer.writerow(d)

        return send_file(app.root_path + 'data.csv', as_attachment=True,
                         attachment_filename='data.csv',
                         mimetype='text/csv', )

    else:
        return jsonify(error='Unsupported export format. Can only format=csv or format=json'), 400