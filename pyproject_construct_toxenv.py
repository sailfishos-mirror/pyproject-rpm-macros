import argparse
import sys


def main(argv):
    parser = argparse.ArgumentParser(
        description='Parse -e arguments instead of RPM getopt.'
    )
    parser.add_argument('-e', '--toxenv', action='append')
    args, _ = parser.parse_known_args(argv)
    return ','.join(args.toxenv)


def strip_x1f(argv):
    r"""
    Hack workaround for RPM 4.20 alpha 2 leaking \x1f (unit separators).
    https://bugzilla.redhat.com/2284187
    """
    return [a.strip('\x1f') for a in argv]


if __name__ == '__main__':
    print(main(strip_x1f(sys.argv[1:])))
