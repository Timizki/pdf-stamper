################################################################################
# app --- Application command line decorator
################################################################################
import os
import sys
import re
import traceback
import inspect

from a4 import get_opts
import a4.log as log


class AppBase:
    def __init__(self, name = None):
        self.name = name
        self.dry = False
        self.debug = False
        self.verbose = False
        self.excode = 0


    def _log(self, msg):
        if self.verbose:
            log.info(msg)
        return self


    def _warn(self, msg):
        log.warn(msg)
        if self.excode < 1:
            self.excode = 1
        return self


    def _err(self, msg):
        log.err(msg)
        if self.excode < 2:
            self.excode = 2
        return self


    def _die_usage(self):
        frame = inspect.getouterframes(inspect.currentframe(), 2)
        app = self.name or os.path.basename(frame[1][1])
        cmd = frame[1][3]
        line = getattr(self, cmd).__doc__.split('\n')[0]
        print(f'Usage: {app} {cmd} {line}')
        sys.exit(2)


def Runnable(UserApp):
    "Turn a class into command line tool with sub-commands."

    class App:
        def __init__(self, **kw):
            self.app = UserApp(**kw)
            self.cmds = sorted([f for f in dir(UserApp) if
                                callable(getattr(UserApp, f)) and
                                not re.match(r'^_', f)])
            self.allcmds = set([f for f in dir(UserApp) if
                                callable(getattr(UserApp, f))])
            self.doc_format = '%%%ds --- %%s' % max(map(len, self.cmds))


        def getdoc(self, cmd, full=False):
            doc = getattr(UserApp, cmd).__doc__
            if full:
                return doc is None and '<no documentation>' or doc.strip()
            if doc is None:
                doc = '<no documentation>'
            lines = doc.split('\n')
            if len(lines) > 1:
                doc = lines[1].strip()
            return self.doc_format % (cmd, doc)


        def _print_global_usage(self):
            name = self.app.name or os.path.basename(sys.argv[0])
            usage = f'Usage: {name} [options] <cmd> [[cmd-options] args ...]\n'
            # app description
            try:
                if self.app.des:
                    usage += f"\n\n       {self.app.des}\n"
            except:
                pass
            usage += ('\n       -n   dry run, change nothing'
                      '\n       -v   be verbose'
                      '\n       -V   turn on debug messages, implies -v'
                      '\n\n       help <command> --- print help for command'
                      '\n\n       ')
            usage += '\n       '.join(map(self.getdoc, self.cmds))
            print(usage, file=sys.stderr)


        def run(self):
            (opts, args) = get_opts('nvV', greedy=False)
            if len(args) < 1:
                self._print_global_usage()
                sys.exit(0)

            self.app.dry = opts['n']
            self.app.debug = opts['V']
            self.app.verbose = self.app.debug or opts['v']
            if self.app.debug:
                log.level('d')

            if args[0] == 'help':
                if len(args) < 2:
                    self._print_global_usage()
                    sys.exit(0)
                cmd = args[1]
                if cmd not in self.cmds:
                    print("Unkown command '%s'" % cmd, file=sys.stderr)
                else:
                    app = self.app.name or os.path.basename(sys.argv[0])
                    print('Usage:  %s %s %s' %
                          (app, cmd, self.getdoc(cmd, True)), file=sys.stderr)
                sys.exit(0)

            cmd = args[0]
            if cmd not in self.cmds:
                print("Unkown command '%s'" % cmd, file=sys.stderr)
                sys.exit(2)
            else:
                if '_init' in self.allcmds:
                    self.app._init()
                tback = None
                try:
                    getattr(self.app, cmd)(args[1:])
                except Exception as e:
                    tback = traceback.format_exc()
                finally:
                    if '_finally' in self.allcmds:
                        self.app._finally()
                    if '_cleanup' in self.allcmds:
                        self.app._cleanup()
                    if tback is None:
                        sys.exit(self.app.excode)
                    else:
                        print(tback, file=sys.stderr)
                        sys.exit(2)
    return App

### a4/app.py ends here
