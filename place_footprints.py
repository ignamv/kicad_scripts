#!/usr/bin/env python2
from os import sys
import pcbnew
import shutil
import argparse
import os
import glob

def wait():
    print('\nPress any key to continue')
    raw_input()

def find_file(extension):
    filename = os.path.join(directory, project_name + '.' + extension)
    if not os.path.exists(filename):
        matches = glob.glob(os.path.join(directory, '*.' + extension))
        if not matches:
            raise IOError('File not found')
        if len(matches) > 1:
            raise IOError('Too many matches')
        return matches[0]
    return filename

parser = argparse.ArgumentParser(description="""\
Modify kicad pcb file to place footprints like in the schematic.
Your project needs to have a .kicad-pcb file with loaded netlist and footprint
associations.""")
parser.add_argument('project', nargs='?', help='Kicad project')
parser.add_argument('--schematic', help='Input .sch file')
parser.add_argument('--pcb', help='Input .kicad_pcb file')
parser.add_argument('--scale', type=float, default=pcbnew.FromMils(1),
                help='Distance scale factor from schematic to PCB (default 1)')
args = parser.parse_args()

if args.schematic and args.pcb:
    schfile = args.schematic
    pcbfile = args.pcb
else:
    if os.path.isfile(args.project):
        # If the user passed the .pro file, extract the directory
        directory = os.path.dirname(args.project)
        project_name = os.path.basename(args.project)
        project_name = project_name[:project_name.rindex('.')]
    else:
        directory = args.project
        try:
            project_name = glob.glob(os.path.join(directory, '*.pro'))[0][:-4]
        except IndexError:
            print('Directory does not have a .pro file')
            wait()
            exit(-1)
    print('Found project ' + project_name)

    try:
        schfile = find_file('sch')
    except IOError as e:
        print('Error searching for .sch file: {}'.format(e))
        wait()
        exit(-1)
    print('Found schematic: ' + schfile)
    try:
        pcbfile = find_file('kicad_pcb')
    except IOError as e:
        print('Error searching for .kicad_pcb file: {}'.format(e))
        wait()
        exit(-1)
    print('Found pcb: ' + pcbfile)

schematic = open(schfile)
board = pcbnew.LoadBoard(pcbfile)

sys.stdout.write('Moving module...')
sys.stdout.flush()
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
    sys.stdout.write(reference + ' ')
    sys.stdout.flush()
sys.stdout.write('\n')

counter = 0
while True:
    try:
        bakfile = pcbfile + '.bak' + str(counter)
        os.stat(bakfile)
        counter += 1
    except:
        break
print('Backing up ' + pcbfile + ' to ' + bakfile)
shutil.copyfile(pcbfile, bakfile)
board.Save(pcbfile)
wait()
