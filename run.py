#!/usr/bin/env python
import os
import sys

from mtp_common.build_tasks.executor import Executor
import build_tasks  # noqa


def main():
    root_path = os.path.abspath(os.path.dirname(__file__))
    exit(Executor(root_path=root_path).run())


def test():
    sys.argv = [os.path.basename(__file__), 'test']
    main()


if __name__ == '__main__':
    if sys.version_info[0:2] < (3, 6):
        raise SystemExit('Python 3.6+ is required')

    main()
