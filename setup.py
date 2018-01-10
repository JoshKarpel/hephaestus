from setuptools import setup, find_packages
import os

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(THIS_DIR, 'README.rst')) as f:
    long_desc = f.read()

setup(
    name = 'hephaestus',
    version = '0.1.0',
    author = 'Josh Karpel',
    author_email = 'josh.karpel@gmail.com',
    # license = '',
    # description = '',
    long_description = long_desc,
    url = 'https://github.com/JoshKarpel/hephaestus',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
    ],
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = [
    ],
    entry_points = """
                [console_scripts]
                heph=hephaestus:cli
            """,
)
