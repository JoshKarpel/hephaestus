import inspect
import sys

import hephaestus as heph

import imported


class Foo:
    def __init__(self, name):
        self.name = name

    def bar(self, clap = '\n', x = 10, a = 'foo'):
        print('bar')

    def selfonly(self):
        pass

    def __repr__(self):
        return self.name

    @classmethod
    def classmethod(cls, a = 5):
        pass

    @staticmethod
    def staticmethod(b = 3):
        pass

    def changename(self):
        self.name = self.name.upper()


def recurse(level):
    print(level)
    if level:
        recurse(level - 1)


def a():
    print('a')
    b()
    recurse(2)
    b()

    foo = Foo('joe')
    foo.bar()
    foo.selfonly()
    foo.classmethod()
    foo.staticmethod()
    foo.changename()  # changes name everywhere because repr is called at printing time
    foo.bar()
    b()

    imported.imported_func()
    imported.imported_func(z = 'kangaroo')


def b():
    print('b')
    c()
    c()


def c():
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
    for _ in range(5):
        c()
    recurse(4)
    tracer.stop()

    print('IF NAME MAIN AFTER WITH', hash(inspect.currentframe()))

    print("\n===== REPORT =====\n")
    with open('report.html', mode = 'w', encoding = 'utf-8') as f:
        f.write(tracer.report_html())
    rep = tracer.report_html()
    print(rep)
