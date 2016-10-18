import Utils
from Utils import printe


class CommandBuilder(object):

    def __init__(self, *command_args):
        self.command_args = list(command_args)

    def append(self, *args):
        for arg in args:
            if isinstance(arg, str):
                self.command_args += [arg]
            elif isinstance(arg, list) or isinstance(arg, tuple):
                for sub_arg in arg:
                    self.append(sub_arg)
            else:
                printe('Error appending argument of unknown type: {}'.format(
                       str(type(arg))), terminate=True)
        return self

    def debug(self):
        return Utils.debug(*self.command_args)

    def run(self, replaceForeground=False):
        return Utils.run(*self.command_args,
                         replaceForeground=replaceForeground)
