import inspect
import sys

import hephaestus as heph


class Foo:
    def bar(self, clap = '\n', x = 10, a = 'foo'):
        print('bar')

    def selfonly(self):
        pass

    def __repr__(self):
        return 'Foo(shazbot)'

    @classmethod
    def classmethod(cls, a = 5):
        pass

    @staticmethod
    def staticmethod(b = 3):
        pass


def recurse(level):
    # print('IN LEVEL', level, hash(inspect.currentframe()))
    print(level)
    joe = 'foo'
    if level:
        recurse(level - 1)


def a():
    # print('IN A', hash(inspect.currentframe()))
    print('a')
    b()
    recurse(2)
    b()

    foo = Foo()
    foo.bar()
    foo.selfonly()
    foo.classmethod()
    foo.staticmethod()
    # b()
    # b()


def b():
    # print('IN B', hash(inspect.currentframe()))
    print('b')
    c()
    # for x in range(2):
    #     c()
    c()
    long()


def c():
    # print('IN C', hash(inspect.currentframe()))
    print('c')


def long():
    x = 0
    for _ in range(1_000_000):
        x += 1

    print(x)


if __name__ == '__main__':
    print('IF NAME MAIN BEFORE WITH', hash(inspect.currentframe()))

    # with heph.Tracer() as tracer:
    #     print('WITH BLOCK', hash(inspect.currentframe()))
    #     a()
    #     recurse(4)

    tracer = heph.Tracer()
    tracer.start()
    a()
    recurse(4)
    tracer.stop()

    print('IF NAME MAIN AFTER WITH', hash(inspect.currentframe()))

    # print(tracer.function_calls)
    print("\n===== REPORT =====\n")
    rep = tracer.report_text()
    print(rep)
