#!/usr/bin/env python3

import argparse
import scipy as sp
from pint import UnitRegistry
import subprocess

def si_prefix_format(number, format="{:.1f} "):
    """Format a number with SI prefixes

    Example: 
    >>> si_prefix_format(33e-5)
    '330.0 µ'
    >>> si_prefix_format(.21e4)
    '2.1 k'"""
    first_power = -15
    power_step = 3
    prefixes = list('fpnµm')+['']+list('kMGT')
    power = sp.floor(sp.log10(number))
    index = max(0, min(len(prefixes) - 1, 
                       int((power - first_power) / power_step)))
    number *= sp.power(10, -first_power - power_step * index)
    return format.format(number) + prefixes[index]

parser = argparse.ArgumentParser(description='Calculate PCB spiral inductor '\
        'with FastHenry and produce Kicad footprint')
Q_ = UnitRegistry().Quantity
parser.add_argument('--width', type=Q_, help='Total outside width', 
        required=True)
parser.add_argument('--height', type=Q_, help='Total outside height',
        required=True)
parser.add_argument('--tracewidth', type=Q_, help='Trace width',
        required=True)
parser.add_argument('--turns', type=int, help='Number of turns', required=True)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--pitch', type=Q_,
        help='Trace pitch (width + separation)')
group.add_argument('--separation', type=Q_, help='Separation between traces')
parser.add_argument('--frequency', type=Q_, help='Operating frequency')
group2 = parser.add_mutually_exclusive_group()
group2.add_argument('--thickness', type=Q_, help='Copper thickness')
group2.add_argument('--areadensity', type=Q_, default=Q_(1,'oz/ft²'),
        help='Copper area density (default 1oz/ft²)')
parser.add_argument('--fasthenry', action='store_true',
        help='Calculate inductance and Q with FastHenry ( '\
                'http://www.fastfieldsolvers.com )')
parser.add_argument('--kicad_mod', type=argparse.FileType('w'),
        help='Save Kicad footprint to this file')
args = parser.parse_args()
if args.fasthenry and args.frequency is None:
    parser.error('Frequency is required for FastHenry analysis')

side1 = args.width.to('mm').magnitude / 2
side2 = args.height.to('mm').magnitude / 2
tracewidth = args.tracewidth.to('mm').magnitude
if args.pitch is not None:
    pitch = args.pitch.to('mm').magnitude
else:
    pitch = args.spacing.to('mm').magnitude + tracewidth
vertices = 4 * args.turns + 1
freq = args.frequency.to('Hz').magnitude
angfreq = 2 * sp.pi * freq
node_indices = sp.arange(vertices)
coordinates = sp.empty((vertices, 3))
if args.thickness is not None:
    thickness = args.thickness.to('mm').magnitude
else:
    copper_density = Q_(8.96, 'g/cm³')
    thickness = (args.areadensity / copper_density).to('mm').magnitude

# Build up the corners
coordinates[0::4,0] = side1 - pitch * sp.arange(args.turns+1)
coordinates[1::4,0] = coordinates[0:-1:4,0]
coordinates[2::4,0] = -coordinates[0:-1:4,0]
coordinates[3::4,0] = -coordinates[0:-1:4,0]
coordinates[0::4,1] = side2 - pitch * sp.arange(args.turns+1)
coordinates[1::4,1] = -coordinates[0:-1:4,1]
coordinates[2::4,1] = -coordinates[0:-1:4,1]
coordinates[3::4,1] = coordinates[0:-1:4,1]
coordinates[0::4,1] += pitch
coordinates[:,2] = 0

# Then connect them
elements = sp.empty((vertices - 1, 4), dtype=float)
elements[:,0] = node_indices[:-1]
elements[:,1] = node_indices[1:]
elements[:,2] = tracewidth
elements[:,3] = thickness

if args.fasthenry:
    process = subprocess.Popen(['/usr/bin/env', 'fasthenry'],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            universal_newlines=True)
    process.stdin.write('*\n.units mm\n\n')
    # Lower coil
    for ii, (x, y, z) in enumerate(coordinates):
        process.stdin.write('N{} x={} y={} z={}\n'.format(ii, x, y, z))
    for ii, (nodeA, nodeB, width, height) in enumerate(elements):
        process.stdin.write('E{} N{} N{} W={} H={}\n'.format(ii, int(nodeA),
            int(nodeB), width, height))
    process.stdin.write('.external N0 N{}\n'.format(vertices - 1))
    # Upper coil
    # TODO: make a decent UI for this
    if False:
        for ii, (x, y, z) in enumerate(coordinates):
            process.stdin.write('N{} x={} y={} z={}\n'.format(ii+vertices, x, y, z+zseparation))
        for ii, (nodeA, nodeB, width, height) in enumerate(elements):
            process.stdin.write('E{} N{} N{} W={} H={}\n'.format(ii, int(nodeA)+vertices, int(nodeB)+vertices, width, height))
        process.stdin.write('.external N{} N{}\n'.format(vertices, 2 * vertices - 1))
        #for line in process.stdout.readlines():
        #    print(line, end='')
    process.stdin.write('.freq fmin={} fmax={} ndec={}\n.end\n'.format(freq, freq, 1))
    process.stdin.close()
    process.wait()
    def stripj(s):
        """Strip trailing 'j' from fasthenry output matrix columns"""
        if s[-1] == ord('j'):
            return s[:-1]
        else:
            return s
    Z = sp.loadtxt('Zc.mat', converters={col: stripj for col in range(2)}, 
        skiprows=2).view(complex)[0]
    L = Z.imag / angfreq
    C = 1 / (angfreq * Z.imag)
    Q = Z.imag / Z.real
    print('Analysis of {}m x {}m {}-turn {}m pitch inductor at {}Hz\n'.format(
        si_prefix_format(side1*2e-3), si_prefix_format(side2*2e-3), args.turns,
        si_prefix_format(pitch*1e-3), si_prefix_format(freq)))
    print('          Inductance: {}H'.format(si_prefix_format(L)))
    print('Resonant capacitance: {}F'.format(si_prefix_format(C)))
    print('                   Q: {:.1e}'.format(Q))

if args.kicad_mod is not None:
    args.kicad_mod.write("""(module PCBAntenna (layer F.Cu)
  (fp_text reference REF** (at 0 0.5) (layer F.SilkS)
    (effects (font (size 1 1) (thickness 0.15)))
  )
  (fp_text value PCBAntenna (at 0 -0.5) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15)))
  )
""")
    for ii, (nodeA, nodeB, width, _) in enumerate(elements):
        args.kicad_mod.write('  (fp_line (start {} {}) (end {} {}) '
                '(layer F.Cu) (width {}))\n'.format(
            coordinates[nodeA,0], coordinates[nodeA,1], 
            coordinates[nodeB,0], coordinates[nodeB,1],
            tracewidth))
    for ii, node in enumerate([0, -1]):
        args.kicad_mod.write('  (pad {} smd rect (at {} {}) (size {} {}) '
                '(layers F.Cu))\n'.format(
            ii+1, coordinates[node,0], coordinates[node,1], 
            elements[node,2], elements[node, 2]))
    args.kicad_mod.write('  (attr smd)\n  (descr "')
    args.kicad_mod.write('PCB inductor {}m x {}m {} turns {}m pitch'.format(
        si_prefix_format(side1*2e-3), si_prefix_format(side2*2e-3), args.turns,
        si_prefix_format(pitch*1e-3)))
    if args.fasthenry:
        args.kicad_mod.write(' inductance {}H Q={:.1e} at {}Hz'.format(
            si_prefix_format(L), Q, si_prefix_format(freq)))
    args.kicad_mod.write(' generated with '\
            'https://github.com/ignamv/kicad_scripts")\n')
    args.kicad_mod.write(')')
    args.kicad_mod.close()
    print('\nFootprint written to ' + args.kicad_mod.name)
