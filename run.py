#!/usr/bin/env python
import os
import sys

from mtp_common.build_tasks.executor import Executor
import build_tasks  # noqa

if sys.version_info[0:2] < (3, 4):
    raise SystemExit('python 3.4+ is required')


def main():
    exit(Executor(root_path=os.path.dirname(__file__)).run())


def test():
    sys.argv = [os.path.basename(__file__), 'test']
    main()


if __name__ == '__main__':
    main()
