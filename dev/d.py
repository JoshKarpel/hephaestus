import inspect
import sys

import hephaestus as heph


def recurse(level):
    print('IN LEVEL', level, hash(inspect.currentframe()))
    print(level)
    if level:
        recurse(level - 1)


def a():
    print('IN A', hash(inspect.currentframe()))
    print('a')
    b()
    recurse(2)


def b():
    print('IN B', hash(inspect.currentframe()))
    print('b')
    for x in range(3):
        c()


def c():
    print('IN C', hash(inspect.currentframe()))
    print('c')


if __name__ == '__main__':
    print('IF NAME MAIN BEFORE WITH', hash(inspect.currentframe()))
    with heph.Tracer() as tracer:
        print('WITH BLOCK', hash(inspect.currentframe()))
        a()
        # recurse(2)
    print('IF NAME MAIN AFTER WITH', hash(inspect.currentframe()))

    # print(tracer.function_calls)
    print("\n===== REPORT =====\n")
    rep = tracer.report(tracer.parent_of_enter_frame_hash)
    print(rep)
