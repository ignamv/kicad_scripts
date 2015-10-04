#!/usr/bin/env python3

import argparse
import math
from fasthenry import coil_impedance
from spiral import squarespiral
from s_expression import SExpression, identifier

def si_prefix_format(number, format="{:.1f} "):
    """Format a number with SI prefixes

    Example: 
    >>> si_prefix_format(33e-5)
    '330.0 µ'
    >>> si_prefix_format(.21e4)
    '2.1 k'"""
    if number == 0:
        return format.format(0)
    first_power = -15
    power_step = 3
    prefixes = list('fpnµm')+['']+list('kMGT')
    power = math.floor(math.log10(number))
    index = max(0, min(len(prefixes) - 1, 
                       int((power - first_power) / power_step)))
    number *= math.pow(10, -first_power - power_step * index)
    return format.format(number) + prefixes[index]

parser = argparse.ArgumentParser(description='Calculate PCB spiral inductor '\
        'with FastHenry and produce Kicad footprint')
parser.add_argument('--width', type=float, help='Total outside width', 
        required=True)
parser.add_argument('--height', type=float, help='Total outside height',
        required=True)
parser.add_argument('--trace_width', type=float, help='Trace width',
        required=True)
parser.add_argument('--mirror', action='store_const', const=-1, default=1,
        help='Reflect footprint horizontally')
parser.add_argument('--turns', type=int, help='Number of turns', required=True)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--pitch', type=float,
        help='Trace pitch (width + separation)')
group.add_argument('--separation', type=float, help='Separation between traces')
parser.add_argument('--zpitch', type=float, default=0.,
        help='Vertical pitch (default 0 for planar inductor)')
parser.add_argument('--frequency', type=float, help='Operating frequency',
        required=True)
group2 = parser.add_mutually_exclusive_group()
group2.add_argument('--thickness', type=float, help='Copper thickness')
group2.add_argument('--weight', type=float, default=1.,
        help='Copper weight per unit area in oz/ft²')
parser.add_argument('--fasthenry', action='store_true',
        help='Calculate inductance and Q with FastHenry ( '\
                'http://www.fastfieldsolvers.com )')
parser.add_argument('--kicad_mod', type=argparse.FileType('w'),
        help='Save Kicad footprint to this file')
parser.add_argument('--pad_size', type=float,
        help='Save Kicad footprint to this file')

units = parser.add_mutually_exclusive_group(required=True)
units.add_argument('--mm', action='store_const', dest='scale', const=1,
        help='Dimensions in millimeters')
units.add_argument('--cm', action='store_const', dest='scale', const=10,
        help='Dimensions in centimeters')
units.add_argument('--mil', action='store_const', dest='scale', const=.0254,
        help='Dimensions in mils = 1in / 1000')
units.add_argument('--in', action='store_const', dest='scale', const=25.4,
        help='Dimensions in inches')

args = parser.parse_args()
if args.fasthenry and args.frequency is None:
    parser.error('Frequency is required for FastHenry analysis')

side1 = args.width * args.scale / 2
side2 = args.height * args.scale / 2
trace_width = args.trace_width * args.scale
if args.pitch is not None:
    pitch = args.pitch
else:
    pitch = args.separation + trace_width
pitch *= args.scale
zpitch = args.zpitch * args.scale
if args.pad_size is None:
    pad_size = trace_width
else:
    pad_size = args.pad_size * args.scale

angfreq = 2 * math.pi * args.frequency

if args.thickness is not None:
    trace_height = args.thickness * args.scale
else:
    # 1 oz/ft² copper is 1.5 mils thick = .03406 mm
    trace_height = args.weight * .03406

coil = list((x * args.mirror, y) for x,y in squarespiral(side1, side2, pitch,
                                                         args.turns))

if args.fasthenry:
    Z = coil_impedance(((x,y,ii*zpitch/4) for ii, (x,y) in enumerate(coil)),
            trace_width, trace_height, args.frequency)
    L = Z.imag / angfreq
    C = 1 / (angfreq * Z.imag)
    Q = Z.imag / Z.real
    print('Analysis of {}m x {}m {}-turn {}m pitch {}m trace inductor at {}Hz\n'.format(
        si_prefix_format(side1*2e-3), si_prefix_format(side2*2e-3), args.turns,
        si_prefix_format(pitch*1e-3), si_prefix_format(trace_width*1e-3),
        si_prefix_format(args.frequency)))
    print('          Inductance: {}H'.format(si_prefix_format(L)))
    print('Resonant capacitance: {}F'.format(si_prefix_format(C)))
    print('                   Q: {:.1e}'.format(Q))

if args.kicad_mod is not None:
    text_effects = SExpression('font', [
        SExpression('size', [1, 1]),
        SExpression('thickness', .15)])
    module = SExpression('module', [
        'PCBAntenna', 
        SExpression('layer', ['F.Cu']),
        SExpression('fp_text', [
            identifier('reference'), 
            'REF**'], [
            ('at', [0, .5]), 
            ('effects', text_effects), 
            ('layer', 'F.SilkS')]),
        SExpression('fp_text', [
            identifier('value'), 
            'PCBAntenna'], [
            ('at', [0, -.5]), 
            ('effects', text_effects),
            ('layer', 'F.SilkS')])])
    module.children.extend(SExpression('fp_line', [], [
        ('start', coil[ii]), ('end', coil[ii + 1]), ('layer', 'F.Cu'),
        ('width', trace_width)]) for ii in range(len(coil) - 1))
    pad_offset = (pad_size - trace_width) / 2
    module.children.append(SExpression('pad', [1, identifier('smd'),
        identifier('rect')], [('at', (coil[0][0] - pad_offset * args.mirror,
            coil[0][1] + pad_offset)), ('size', [pad_size, pad_size]),
            ('layers', 'F.Cu')]))
    module.children.append(SExpression('pad', [2, identifier('smd'),
        identifier('rect')], [('at', (coil[-1][0] - pad_offset * args.mirror,
            coil[-1][1] - pad_offset)), ('size', [pad_size, pad_size]),
            ('layers', 'F.Cu')]))
    descr = 'PCB inductor {}m x {}m {} turns {}m pitch'.format(
        si_prefix_format(side1*2e-3), si_prefix_format(side2*2e-3), 
        args.turns, si_prefix_format(pitch*1e-3))
    if args.fasthenry:
        descr += ' inductance {}H Q={:.1e} at {}Hz'.format(
            si_prefix_format(L), Q, si_prefix_format(args.frequency))
    descr += ' generated with https://github.com/ignamv/kicad_scripts'
    module.children.append(SExpression('descr', descr))
    module.write_to_stream(args.kicad_mod)
    args.kicad_mod.close()
    print('\nFootprint written to ' + args.kicad_mod.name)
