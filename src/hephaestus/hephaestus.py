import inspect
import sys
import functools
import collections


# class FunctionCall:
#     def __init__(self, name, frame_hash):
#         self.name = name
#         self.frame_hash = frame_hash
#
#     def __repr__(self):
#         return f'{self.name}@{self.frame_hash}'


class Node:
    def __init__(self, frame_hash, parent_frame_hash, frame):
        self.frame_hash = frame_hash
        self.parent = parent_frame_hash
        self.frame = frame
        self.children = []
        self.calls = []

    def __hash__(self):
        return self.frame_hash

    def __repr__(self):
        return f'{self.frame.f_code.co_name}'

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

        parent = frame.f_back

        try:
            node = tracer.frame_hash_to_node[hash(frame)]
        except KeyError:
            node = Node(hash(frame), hash(parent), frame)
            tracer.frame_hash_to_node[hash(frame)] = node

        tracer.frame_hash_to_node[hash(parent)].children.append(node)


def get_parent_frame(frame):
    return inspect.getouterframes(frame)[1].frame


class Tracer:
    def __init__(self):
        self.function_calls = collections.defaultdict(list)
        self.frame_hash_to_node = {}

    def __enter__(self):
        parent = get_parent_frame(inspect.currentframe())
        self.parent_of_enter_frame_hash = hash(get_parent_frame(inspect.currentframe()))
        self.enter_frame_hash = hash(inspect.currentframe())
        print('PARENT OF ENTER FRAME', self.parent_of_enter_frame_hash)
        print('ENTER FRAME', self.enter_frame_hash)
        sys.setprofile(functools.partial(tracefunc, tracer = self))

        self.root_node = Node(self.parent_of_enter_frame_hash, None, parent)
        self.frame_hash_to_node[hash(self.root_node)] = self.root_node

        print(self.frame_hash_to_node)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.setprofile(None)
        self.exit_frame_hash = hash(inspect.currentframe())
        print('EXIT FRAME', self.exit_frame_hash)

    def report(self):
        rep = self.root_node.report()
        rep = ['│' + line[1:] for line in rep.split('\n')]
        return '\n'.join(('┌─ <START TRACE>', *rep, '└─ <END TRACE>'))
