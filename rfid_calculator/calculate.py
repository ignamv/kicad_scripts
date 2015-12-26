#!/usr/bin/env python3
import werkzeug.exceptions
import flask
import math
application = flask.Flask(__name__)

from spiral import spiral
from fasthenry import coil_impedance
from trace_footprint import write_trace_footprint
from subprocess import TimeoutExpired
import functools
import os
os.chdir('/var/www/spiral')

@application.route('/')
def root():
    return flask.render_template('form.html')

def parse_check(field, converter, condition = None):
    try:
        raw = flask.request.values[field]
    except werkzeug.exceptions.BadRequestKeyError:
        raise Exception('Missing ' + field)
    try:
        if isinstance(converter, dict):
            ret = converter[raw]
        elif callable(converter):
            ret = converter(raw)
    except:
        raise Exception('Invalid ' + field)
    if condition is not None and not condition(ret):
        raise ValueError('Invalid ' + field)
    return ret

def ajax_fallback(ajax_template, fallback_template):
    def wrap(function):
        @functools.wraps(function)
        def wrapper():
            parameters = function()
            if not isinstance(parameters, dict):
                # Error or redirection
                return parameters
            ajax = flask.request.form.get('ajax', type=bool, default=False)
            return flask.render_template(
                    [fallback_template, ajax_template][ajax], **parameters)
        return wrapper
    return wrap

def format_si_prefix(number, format="{:.1f} "):
    """Format a number with SI prefixes

    Example: 
    >>> si_prefix_format(33e-5)
    '330.0 µ'
    >>> si_prefix_format(.21e4)
    '2.1 k'"""
    first_power = -15
    power_step = 3
    prefixes = list('fpnµm')+['']+list('kMGT')
    power = math.floor(math.log10(number))
    index = max(0, min(len(prefixes) - 1, 
                       int((power - first_power) / power_step)))
    number *= math.pow(10, -first_power - power_step * index)
    return format.format(number) + prefixes[index]

def parse_spiral_request():
    valid_units = {'mm': 1, 'cm': 10, 'mil': .0254, 'in': 25.4}
    units = parse_check('units', valid_units)
    def dimension(string):
        return units * float(string)
    width = parse_check('width', dimension, lambda x: x > 0)
    height = parse_check('height', dimension, lambda x: x > 0)
    turns = parse_check('turns', int, lambda x: x > 0 and x < 100)
    pitch = parse_check('pitch', dimension, lambda x: 2*x*turns < width and 
                                                  2*x*turns < height)
    return dict(units='mm', width=width, height=height, turns=turns, pitch=pitch,
            trace_width=parse_check('trace_width', dimension, 
                lambda x: x > 0 and x < pitch),
            trace_height=parse_check('trace_height', dimension,
                lambda x: x > 0),
            pad_size = parse_check('pad_size', dimension, lambda x: x > 0),
            frequency=parse_check('frequency', float, lambda x: x > 0))

@application.route('/calculate', methods=['POST'])
@ajax_fallback('results.html', 'results_fallback.html')
def calculate():
    if flask.request.values.get('download', type=bool, default=False):
        return footprint()
    try:
        args = parse_spiral_request()
    except Exception as e:
        return dict(success=False, error=str(e))
    args['width'] -= args['trace_width']
    args['height'] -= args['trace_width']
    coil = ((x, y, 0) for x,y in spiral(args['width']/2, args['height']/2,
        args['pitch'], args['turns']))
    try:
        impedance = coil_impedance(coil, args['trace_width'],
        args['trace_height'],
        args['frequency'], 
        './fasthenry')
    except TimeoutExpired:
        return dict(success=False, error='Calculations took too long')
    angfreq = 2 * math.pi * args['frequency']
    resistance = format_si_prefix(impedance.real) + 'Ω'
    inductance = format_si_prefix(impedance.imag / angfreq) + 'H'
    qfactor = '{:.2g}'.format(impedance.imag / impedance.real)
    capacitance = format_si_prefix(1 / (angfreq * impedance.imag)) + 'F'
    args.update(resistance=resistance, inductance=inductance, qfactor=qfactor,
            capacitance=capacitance)
    return dict(success=True, resistance=resistance, inductance=inductance,
            qfactor=qfactor, capacitance=capacitance,
            download=flask.url_for('footprint', **args))

@application.route('/footprint', methods=['GET'])
def footprint():
    try:
        args = parse_spiral_request()
    except Exception as e:
        return flask.render_template('error.html', error=str(e))
    args['width'] -= args['trace_width']
    args['height'] -= args['trace_width']
    inductance = flask.request.values.get('inductance', default='')
    resistance = flask.request.values.get('resistance', default='')
    qfactor = flask.request.values.get('qfactor', default='')
    capacitance = flask.request.values.get('capacitance', default='')
    coil = list(spiral(args['width']/2, args['height']/2, args['pitch'],
        args['turns']))
    description = 'PCB inductor {}m x {}m {} turns {}m pitch'.format(
        format_si_prefix(args['width']*1e-3),
        format_si_prefix(args['height']*1e-3), 
        args['turns'], format_si_prefix(args['pitch']*1e-3))
    description += ' inductance {} Q={} at {}Hz'.format(
            inductance, qfactor, args['frequency'])
    description += ' generated with https://github.com/ignamv/kicad_scripts'
    response = flask.Response(mimetype='text/plain',
            headers=[('Content-disposition',
                'attachment; filename = pcbantenna.kicad_mod')])
    write_trace_footprint(response.stream, 'PCBAntenna', description,
            coil, args['trace_width'], args['pad_size'])
    return response

if __name__ == '__main__':
    application.run(debug=True)
