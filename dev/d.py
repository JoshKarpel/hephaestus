import inspect
import sys

import hephaestus as heph


class Foo:
    def bar(self, clap = '\n'):
        print('bar')

    def __repr__(self):
        return 'shazbot'


def recurse(level):
    print('IN LEVEL', level, hash(inspect.currentframe()))
    print(level)
    joe = 'foo'
    if level:
        recurse(level - 1)


def a():
    print('IN A', hash(inspect.currentframe()))
    print('a')
    b()
    recurse(2)
    b()

    foo = Foo()
    foo.bar()
    # b()
    # b()


def b():
    print('IN B', hash(inspect.currentframe()))
    print('b')
    c()
    # for x in range(2):
    #     c()
    c()


def c():
    print('IN C', hash(inspect.currentframe()))
    print('c')


if __name__ == '__main__':
    print('IF NAME MAIN BEFORE WITH', hash(inspect.currentframe()))
    with heph.Tracer() as tracer:
        print('WITH BLOCK', hash(inspect.currentframe()))
        a()
        recurse(4)
    print('IF NAME MAIN AFTER WITH', hash(inspect.currentframe()))

    # print(tracer.function_calls)
    print("\n===== REPORT =====\n")
    rep = tracer.report()
    print(rep)
