#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import time


class Utils(object):

    def printe(*objects, terminate=False, sep=' ', end='\n', file=sys.stderr,
               flush=False):
        print(*objects, sep=sep, end=end, file=file, flush=flush)
        if terminate:
            if isinstance(terminate, int):
                sys.exit(terminate)
            sys.exit(1)

    def debug(*command_args, terminate_on_fail=False):
        print('DEBUG:  ', end='')
        print(' '.join(command_args))
        return '$(%s)' % ' '.join(command_args)

    def run(*command_args, terminate_on_fail=False, replaceForeground=False):
        if os.environ.get('UTILS_DEBUG') == 'true' \
                or os.environ.get('UTILS_DEBUG') == 'True':
            return Utils.debug(*command_args,
                               terminate_on_fail=terminate_on_fail)
        try:
            if replaceForeground:
                os.execvp(command_args[0], command_args)
            output = subprocess.check_output(command_args,
                                             universal_newlines=True)
            if output.endswith('\n'):
                output = output[:-1]
            return output
        except KeyboardInterrupt:
            printe('Keyboard Interrupt fired.')
        except:
            try:
                exit_status = int(re.search("[0-9]+$",
                                            str(sys.exc_info()[1])).group(0))
                printe('Exit code: ' + str(exit_status))
            except:
                printe('Exited without valid error code.')
            printe(end='', terminate=exit_status)

    """Returns the terminal size as an array of [ rows, columns ]"""
    def terminal_size():
        result = run('stty', 'size').split()
        if len(result) == 2:
            try:
                return [int(result[0]), int(result[1])]
            except:
                return [-1, -1]

    epoch = time.time

printe = error = Utils.printe
run = Utils.run
debug = Utils.debug
epoch = Utils.epoch
terminal_size = Utils.terminal_size
