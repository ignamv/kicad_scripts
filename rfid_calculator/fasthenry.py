import subprocess
import os

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

