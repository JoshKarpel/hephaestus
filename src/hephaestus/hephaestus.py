import inspect
import sys
import functools
import collections
import gc
import copy
import os
import time


class Node:
    def __init__(self, frame_hash, parent_frame, frame):
        self.frame_hash = frame_hash
        self.parent = parent_frame
        self.frame = frame
        self.children = []
        self.calls = []
        self.locals = dict(self.frame.f_locals)  # dict freezes it just after function call, before any other local variables can be created!
        self.start_time = None
        self.elapsed_time = None

    def __hash__(self):
        return self.frame_hash

    def __repr__(self):
        pre = ''
        if 'self' in self.locals:
            pre = self.locals['self'].__class__.__name__ + '.'
        elif 'cls' in self.locals:
            pre = self.locals['cls'].__name__ + '.'

        args = ', '.join(fr'{arg} = {repr(val)}'.replace('\n', '')
                         for arg, val
                         in reversed(tuple(self.locals.items()))
                         if arg not in ('cls',))

        own_time = self.elapsed_time - sum(child.elapsed_time for child in self.children)

        return fr'{pre}{get_function_name(self.frame)}({args}) | {self.elapsed_time:6f} s | {own_time:6f} s'

    def report(self):
        lines = self._lines()
        lines = self._cleanup(lines)
        return '\n'.join(lines)

    def _lines(self):
        lines = []
        for child, report in ((child, child.report()) for child in self.children):
            lines.append(f'├─ {str(child)}')
            if report != '':
                lines.extend(f'│  {line}' for line in report.split('\n'))

        return lines

    def _cleanup(self, lines):
        for index, line in reversed(list(enumerate(lines))):
            if line[0] == '├':  # this is the last branch on this level, replace it with endcap and break
                lines[index] = line.replace('├', '└')
                break
            else:  # not yet at last branch, continue cleanup
                lines[index] = line.replace('│', ' ', 1)

        return lines


def get_parent_frame(frame):
    return frame.f_back


def get_function_name(frame):
    return frame.f_code.co_name


def get_file_name(frame):
    return os.path.basename(frame.f_code.co_filename)


class TraceFunction:
    def __init__(self, tracer, ignored_funcnames = (), ignored_filenames = (), timing_func = time.perf_counter):
        self.tracer = tracer
        self.ignored_funcnames = ignored_funcnames
        self.ignored_filenames = ('hephaestus.py',) + ignored_filenames
        self.timing_func = timing_func

    def __call__(self, frame, event, arg):
        if get_function_name(frame) in self.ignored_funcnames:
            return
        if get_file_name(frame) in self.ignored_filenames:
            return

        if event == 'call':
            parent = frame.f_back

            try:
                node = self.tracer.frame_hash_to_node[hash(frame)]
            except KeyError:
                node = Node(hash(frame), parent, frame)
                self.tracer.frame_hash_to_node[hash(frame)] = node

            self.tracer.frame_hash_to_node[hash(parent)].children.append(node)

            node.start_time = self.timing_func()

        if event == 'return':
            node = self.tracer.frame_hash_to_node[hash(frame)]
            node.elapsed_time = self.timing_func() - node.start_time


class Tracer:
    def __init__(self):
        self.frame_hash_to_node = {}

    def __enter__(self):
        parent = get_parent_frame(inspect.currentframe())

        sys.setprofile(TraceFunction(self))

        self.root_node = Node(hash(parent), get_parent_frame(parent), parent)
        self.frame_hash_to_node[hash(parent)] = self.root_node

        return self

    start = __enter__

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        sys.setprofile(None)

    def report(self):
        proto_report = self.root_node.report()

        # make sure we've got a solid line on far left
        rep_lines = ['│' + line[1:] for line in proto_report.split('\n')]

        rep = '\n'.join((
            '┌─<START>',
            *rep_lines,
            '└─<END>',
        ))

        return rep
