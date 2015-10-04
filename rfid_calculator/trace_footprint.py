from s_expression import SExpression, identifier

def write_trace_footprint(stream, name, description, vertices, trace_width, 
        pad_size, mirror=False):
    mirror = [1, -1][mirror]
    text_effects = SExpression('font', [SExpression('size', [1, 1]),
        SExpression('thickness', .15)])
    module = SExpression('module', [name,
        SExpression('layer', ['F.Cu']),
        SExpression('fp_text', [identifier('reference'), 'REF**'],
            [('at', [0, .5]), ('effects', text_effects), ('layer', 'F.SilkS')]),
        SExpression('fp_text', [identifier('value'), name],
            [('at', [0, -.5]), ('effects', text_effects),
                ('layer', 'F.SilkS')])])
    module.children.extend(SExpression('fp_line', [], [
        ('start', vertices[ii]), ('end', vertices[ii + 1]), ('layer', 'F.Cu'),
        ('width', trace_width)]) for ii in range(len(vertices) - 1))
    pad_offset = (pad_size - trace_width) / 2
    module.children.append(SExpression('pad', [1, identifier('smd'),
        identifier('rect')], [('at', (vertices[0][0] - pad_offset * mirror,
            vertices[0][1] + pad_offset)), ('size', [pad_size, pad_size]),
            ('layers', 'F.Cu')]))
    module.children.append(SExpression('pad', [2, identifier('smd'),
        identifier('rect')], [('at', (vertices[-1][0] - pad_offset * mirror,
            vertices[-1][1] - pad_offset)), ('size', [pad_size, pad_size]),
            ('layers', 'F.Cu')]))
    module.children.append(SExpression('descr', description))
    module.write_to_stream(stream)
