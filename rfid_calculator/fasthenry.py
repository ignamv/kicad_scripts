import subprocess
import os
import sys
import io

class Fasthenry(object):

    class MissingNodeException(Exception):
        pass

class InputFile(io.StringIO):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.elements = 0
        self.write('*\n')
    @staticmethod
    def node(name, x, y, z):
        return name + ' x={} y={} z={}'.format(x, y, z)

    @staticmethod
    def element(name, node1, node2, width, height, 
            width_filaments, height_filaments):
        return name + ' ' + node1 + ' ' + node2 + \
                ' w={} h={} nwinc={} nhinc={}'.format(width, height,
                        width_filaments, height_filaments)

    @staticmethod
    def external(name, node1, node2):
        return ' '.join(['.external', node1, node2, name])

    @staticmethod
    def sweep(min_frequency, max_frequency, points_per_decade):
        return '.freq fmin={} fmax={} ndec={}'.format(min_frequency,
                max_frequency, points_per_decade)

    def addnode(self, x, y, z):
        name = 'n{}'.format(len(self.nodes))
        self.write(self.node(name, x, y, z))
        self.nodes.append(name)
        return name

    def addelement(self, node1, node2, width, height, width_filaments,
            height_filaments):
        if node1 not in self.nodes or node2 not in self.nodes:
            raise Fasthenry.MissingNodeException()
        name = 'e{}'.format(self.elements)
        self.write(self.element(name, node1, node2, width, height,
            width_filaments, height_filaments))
        self.elements += 1
        return name

    def addport(self, name, node1, node2):
        if node1 not in self.nodes or node2 not in self.nodes:
            raise Fasthenry.MissingNodeException()
        self.write(self.external(name, node1, node2))

    #def addcoil(self, name, vertices, width, height, width_filaments,
            #height_filaments


def coil_impedance(vertices, trace_width, trace_height, frequency):
    process = subprocess.Popen(['./fasthenry'],
            stdin=subprocess.PIPE, 
            stdout=open('fasthenry.log', 'w'),
            universal_newlines=True)
    process.stdin.write('*\n.units mm\n\n')
    last_vertex = -1
    for ii, (x, y, z) in enumerate(vertices):
        process.stdin.write('N{} x={} y={} z={}\n'.format(ii, x, y, z))
        last_vertex = ii
    for ii in range(last_vertex):
        process.stdin.write('E{} N{} N{} W={} H={} nhinc={} nwinc={}\n'.format(
            ii, ii, ii + 1, trace_width, trace_height, 
            max(1, int(trace_width/1)), 1))
    process.stdin.write('.external N0 N{}\n'.format(last_vertex))
    process.stdin.write('.freq fmin={} fmax={} ndec={}\n.end\n'.format(
        frequency, frequency, 1))
    process.stdin.close()
    try:
        process.wait(10)
    except subprocess.TimeoutExpired as e:
        process.terminate()
        raise e
    filename = 'Zc.mat'
    fd = open(filename, 'r')
    fd.readline()
    fd.readline()
    parts = fd.readline().split()
    fd.close()
    os.remove(filename)
    return complex(float(parts[0]), float(parts[1][:-1]))

