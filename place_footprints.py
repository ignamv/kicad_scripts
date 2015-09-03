#!/usr/bin/env python2
from os import sys
import pcbnew
import argparse

parser = argparse.ArgumentParser(description=
    'Modify kicad pcb file to place footprints like in the schematic')
parser.add_argument('--scale', type=float, default=pcbnew.FromMils(1),
        help='Distance scale factor from schematic to PCB (default 1)')
parser.add_argument('schematic', help='Input .sch file')
parser.add_argument('pcbin', help='Input .kicad-pcb file')
parser.add_argument('pcbout', help='Output .kicad-pcb file')
args = parser.parse_args()

schematic = open(args.schematic)
board = pcbnew.LoadBoard(args.pcbin)

while True:
    line = schematic.readline()
    if not line:
        # End of file
        break
    if line != "$Comp\n":
        # Loop until module is found
        continue
    # From https://en.wikibooks.org/wiki/Kicad/file_formats
    line = schematic.readline()
    if line[0] != 'L':
        raise RuntimeError('Expected component reference line, got '+line[:-1])
    reference = line[:-1].split(' ')[2]
    schematic.readline()
    line = schematic.readline()
    if line[0] != 'P':
        raise RuntimeError('Expected component position line, got '+line[:-1])
    x, y = map(lambda s: args.scale * float(s), line[:-1].split(' ')[1:3])
    module = board.FindModuleByReference(reference)
    if module is None:
        # Probably a power symbol
        continue
    module.SetPosition(pcbnew.wxPoint(x, y))

board.Save(args.pcbout)
