import argparse


# look at coverage.py for this
def parse_arguments(**kwargs):
    parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        'file',
        type = str,
        help = 'the file to run',
    )

    return parser.parse_args()
