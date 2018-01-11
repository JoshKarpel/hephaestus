import inspect
import sys

import hephaestus as heph


class Foo:
    def bar(self, clap = '\n', x = 10, a = 'foo'):
        print('bar')

    def selfonly(self):
        pass

    def __repr__(self):
        return 'shazbot'

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
    # recurse(2)
    # b()

    # foo = Foo()
    # foo.bar()
    # foo.selfonly()
    # foo.classmethod()
    # foo.staticmethod()
    # b()
    # b()


def b():
    # print('IN B', hash(inspect.currentframe()))
    print('b')
    c()
    # for x in range(2):
    #     c()
    # c()


def c():
    # print('IN C', hash(inspect.currentframe()))
    print('c')


if __name__ == '__main__':
    print('IF NAME MAIN BEFORE WITH', hash(inspect.currentframe()))

    # with heph.Tracer() as tracer:
    #     print('WITH BLOCK', hash(inspect.currentframe()))
    #     a()
    #     recurse(4)

    tracer = heph.Tracer()
    tracer.start()
    a()
    a()
    # recurse(4)
    tracer.stop()

    print('IF NAME MAIN AFTER WITH', hash(inspect.currentframe()))

    # print(tracer.function_calls)
    print("\n===== REPORT =====\n")
    with open('report.html', mode = 'w', encoding = 'utf-8') as f:
        f.write(tracer.report_html())
    rep = tracer.report_html()
    print(rep)
