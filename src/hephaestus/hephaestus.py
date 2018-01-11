import inspect
import sys
import functools
import collections
import gc
import copy


class Node:
    def __init__(self, frame_hash, parent_frame, frame):
        self.frame_hash = frame_hash
        self.parent = parent_frame
        self.frame = frame
        self.children = []
        self.calls = []
        self.locals = dict(self.frame.f_locals)  # dict freezes it just after function call, before any other local variables can be created!

    def __hash__(self):
        return self.frame_hash

    def __repr__(self):
        args = ', '.join(f'{arg} = {repr(val)}' for arg, val in self.locals.items())

        pre = ''
        if 'self' in self.locals:
            pre = self.locals['self'].__class__.__name__ + '.'

        return f'{pre}{self.frame.f_code.co_name}({args})'

    def report(self):
        lines = []
        for child, report in ((child, child.report()) for child in self.children):
            lines.append(f'├─ {str(child)}')
            lines.extend('│  ' + line for line in report.split('\n') if line != '')

        lines = self._cleanup(lines)
        return '\n'.join(lines)

    def _cleanup(self, lines):
        for index, line in reversed(list(enumerate(lines))):
            if line[0] == '├':  # this is the last branch on this level, replace it with endcap and break
                lines[index] = line.replace('├', '└')
                break
            else:  # not yet at last branch, continue cleanup
                lines[index] = line.replace('│', ' ', 1)

        return lines


def tracefunc(frame, event, arg, tracer):
    if event == 'call':
        if frame.f_code.co_name in ('currentframe',):  # ignore calls to inspect.currentframe()
            return
        if 'hephaestus.py' in frame.f_code.co_filename:  # ignore any function calls in this module
            return

        # print(frame.f_locals)
        # print(frame.f_code)
        # print(frame.f_code.co_varnames)
        # print(inspect.signature(frame.f_code))

        parent = frame.f_back

        # func = parent.f_globals[frame.f_code.co_name]
        # print(func)
        # print(type(inspect.signature(func)))
        # print(tuple(inspect.signature(func).parameters.keys()))

        # func = giveupthefunc(frame)
        # print(func)

        try:
            node = tracer.frame_hash_to_node[hash(frame)]
        except KeyError:
            node = Node(hash(frame), parent, frame)
            tracer.frame_hash_to_node[hash(frame)] = node

        # print(tracer.frame_hash_to_node.keys())
        tracer.frame_hash_to_node[hash(parent)].children.append(node)


def get_parent_frame(frame):
    return frame.f_back


class Tracer:
    def __init__(self):
        self.function_calls = collections.defaultdict(list)
        self.frame_hash_to_node = {}

    def __enter__(self):
        parent = get_parent_frame(inspect.currentframe())

        sys.setprofile(functools.partial(tracefunc, tracer = self))

        # self.root_node = Node(hash(parent), None, parent)
        self.root_node = Node(hash(parent), get_parent_frame(parent), parent)
        self.frame_hash_to_node[hash(parent)] = self.root_node

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.setprofile(None)

    def report(self):
        rep = self.root_node.report()
        rep = ['│' + line[1:] for line in rep.split('\n')]
        return '\n'.join(('┌─ <START TRACE>', *rep, '└─ <END TRACE>'))


def giveupthefunc(frame):
    code = frame.f_code
    globs = frame.f_globals
    functype = type(lambda: 0)
    funcs = []
    for func in gc.get_referrers(code):
        if type(func) is functype:
            if getattr(func, "func_code", None) is code:
                if getattr(func, "func_globals", None) is globs:
                    funcs.append(func)
                    if len(funcs) > 1:
                        return None
    return funcs[0] if funcs else None
