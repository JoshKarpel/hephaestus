import inspect
import sys
import functools
import collections


class FunctionCall:
    def __init__(self, name, frame_hash):
        self.name = name
        self.frame_hash = frame_hash

    def __repr__(self):
        return f'{self.name}@{self.frame_hash}'


def tracefunc(frame, event, arg, tracer):
    if event == 'call':
        if frame.f_code.co_name in ('currentframe',):  # ignore calls to inspect.currentframe()
            return
        print(frame.f_code.co_filename)
        if 'hephaestus.py' in frame.f_code.co_filename:  # ignore any function calls in this module
            return
        parent = inspect.getouterframes(frame)[1].frame
        depth = len(inspect.getouterframes(frame))
        print(hash(frame), hash(parent), event, frame.f_code.co_name, arg)
        tracer.function_calls[hash(parent)].append(FunctionCall(frame.f_code.co_name, hash(frame)))


def get_parent_frame(frame):
    return inspect.getouterframes(frame)[1].frame


class Tracer:
    def __init__(self):
        self.function_calls = collections.defaultdict(list)

    def __enter__(self):
        self.parent_of_enter_frame_hash = hash(get_parent_frame(inspect.currentframe()))
        self.enter_frame_hash = hash(inspect.currentframe())
        print('PARENT OF ENTER FRAME', self.parent_of_enter_frame_hash)
        print('ENTER FRAME', self.enter_frame_hash)
        sys.setprofile(functools.partial(tracefunc, tracer = self))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.setprofile(None)
        self.exit_frame_hash = hash(inspect.currentframe())
        print('EXIT FRAME', self.exit_frame_hash)
        # self.function_calls.pop(hash(exit_frame), None)
        return

    def report(self, frame_hash, depth = 0):
        lines = self.make_lines(frame_hash, [], depth = depth)
        # lines = self._cleanup(lines)
        rep = '\n'.join(lines)

        return rep

    def make_lines(self, frame_hash, lines, depth = 0):
        print(lines)
        for index, fn_call in enumerate(self.function_calls[frame_hash]):
            # if index != len(self.function_calls[frame_hash]) - 1:
            middle = ('├─ ' if depth != 0 else '')
            # else:
            #     middle = ('└─ ' if depth != 0 else '')
            lines.append('│  ' * (depth - 1) + middle + str(fn_call))
            # lines.extend('│  ' + line for line in self.make_lines(fn_call.frame_hash, lines, depth = depth + 1))
            lines = self.make_lines(fn_call.frame_hash, lines, depth = depth + 1)
            # lines = self._cleanup(lines)
            lines[-1].replace('├', '└')

        return lines

    def _cleanup(self, lines):
        # this loop goes over the field strings in reverse, cleaning up the tail of the structure indicators
        for index, line in reversed(list(enumerate(lines))):
            print(index, line)
            if line[0] == '└':  # this is the last branch on this level, replace it with endcap and break
                lines[index] = line.replace('├', '└')
                break
            else:  # not yet at last branch, continue cleanup
                lines[index] = line.replace('│', ' ', 1)

        return lines
