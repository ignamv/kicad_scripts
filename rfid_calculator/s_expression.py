
class SExpression(object):
    def __init__(self, tag, children=None, childexpr=None):
        self.tag = tag
        if isinstance(children, list) or isinstance(children, tuple):
            self.children = children
        elif children is None:
            self.children = []
        else:
            self.children = [children]
        if childexpr is None:
            return
        for childtag, value in childexpr:
            self.children.append(SExpression(childtag, value))
    
    def write_to_stream(self, stream, indent=0):
        stream.write('(' + self.tag + '\n')
        for child in self.children:
            stream.write('  ' * (indent + 1))
            if isinstance(child, float):
                stream.write('{:e}'.format(child))
            elif isinstance(child, int):
                stream.write('{:d}'.format(child))
            elif isinstance(child, str):
                stream.write('"' + child + '"')
            elif isinstance(child, SExpression):
                child.write_to_stream(stream, indent+1)
            else:
                raise Exception('Can\'t format child', child)
            stream.write('\n')
        stream.write('  '*indent+')')

class identifier(SExpression):
    def __init__(self, name):
        super().__init__(name)

    def write_to_stream(self, stream, indent=0):
        stream.write(self.tag + '\n')

