__all__ = [ 'die'
          , 'die_usage'
          , 'parse_range'
          , 'parse_date'
          , 'parse_date_range'
          , 'parse_url'
          , 'get_opts'
          , 'parse_opts'
          ]


if __name__ == '__main__':
    MyApp().run()


import sys
import os
import re
import getopt
import datetime as dt
from calendar import monthrange
from collections.abc import MutableMapping


def die(msg):
    isatty = sys.stderr.isatty()
    prefix = '\033[31m' if isatty else ''
    suffix = '\033[00m' if isatty else ''
    sys.stderr.write(f'{prefix}{msg}\n{suffix}')
    sys.exit(2)


def die_usage(spec, *, name = None):
    if name is None:
        name = os.path.basename(sys.argv[0])
        if name.startswith('__main__.'):
            name = os.path.basename(os.path.dirname(sys.argv[0]))
    sys.stdout.write(f'Usage: {name} [options] ')
    for line in spec.strip().split('\n'):
        if line and line[0] == '-':
            print('   ', line)
        else:
            print(line)
    sys.exit(2)


def parse_range(spec, *, sep='-', comma=','):
    if comma and comma in spec:
        return [parse_range(s, sep=sep, comma=comma) for s in spec.split(comma)]
    ret = spec.split(sep)
    if len(ret) == 1:
        return [spec, spec]
    if len(ret) > 2:
        return ret[1:2]
    if len(ret) == 2:
        beg, end = ret
        if len(beg) > len(end):
            ret = [beg, beg[0:(len(beg)-len(end))] + end]
    return ret


def parse_date(spec, *, to_str = False, cal = 0):
    """Accpets:
    yyyy[-]mm[-]dd, this, today, yest[N], tomo[N]
    """

    dnum = None
    dstr = spec.replace('-', '').replace('/', '')
    if re.match(r'^\d{8}$', dstr):
        dnum = int(dstr)
    else:
        now = dt.datetime.now()
        dnum = int(now.strftime('%Y%m%d'))
        mo = re.match(r'(yest|tomo)(\d+)?', dstr)
        if mo:
            if mo.group(1) == 'yest':
                shift = -int(mo.group(2)) if mo.group(2) else -1
            else:
                shift =  int(mo.group(2)) if mo.group(2) else  1
            ts = dt.datetime.now() + dt.timedelta(days = shift)
            dnum = int(ts.strftime('%Y%m%d'))
        elif dstr != 'today' and dstr != 'this':
            raise ValueError(f'inavlid date spec {spec}')

    return str(dnum) if to_str else dnum


def parse_date_range(spec, *, sep='-'):
    beg, end = parse_range(spec, sep=sep, comma=None)
    if int(beg) > int(end):
        raise ValueError('Invalid date range spec')

    if len(beg) == 4:
        beg = beg + '0101'
    elif len(beg) == 6:
        beg = beg + '01'

    if len(end) == 4:
        end = int(end + '1231')
    elif len(end) == 6:
        end = int(end) * 100 + monthrange(int(end[:4]), int(end[4:]))[1]
    else:
        end = int(end)

    return (int(beg), end)


def parse_url(url, **kw):
    "Parse URL to dict[str, str], tolerate special characters in password"
    ret = {}
    if url.find('://') >= 0:
        (ret['proto'], url) = url.split('://')
    i = url.rfind('@')
    if i >= 0:
        auth = url[:i]
        url = url[i+1:]
        j = auth.find(':')
        if j < 0:
            ret['user'] = auth
        else:
            ret['user'] = auth[:j]
            ret['pass'] = auth[j+1:]
    mo = re.match(r'^([^:/?]+)(:(\d+))?([/?](.+))?$', url)
    if mo is not None:
        host, port, path = (mo.group(1), mo.group(3), mo.group(4))
        ret['host'] = host
        if port is not None:
            try:
                ret['port'] = int(port)
            except ValueError:
                ret['port'] = port
        if path is not None:
            params = None
            first = path[0]
            path = path[1:].strip('/').strip('?')
            if first == '?':
                params = path.split(',')
            else:
                pm = re.match(r'^([^?]+)\?(.+)$', path)
                if pm:
                    path = pm.group(1).strip('/')
                    params = pm.group(2).split(',')
                ret['path'] = path.split('/')
            if params:
                ret['param'] = {x[0]: x[1]
                                for x in [p.split('=') for p in params]
                                if len(x) == 2}
                if not ret['param']:
                    del ret['param']
    for k in ['proto', 'user', 'pass', 'host', 'port', 'path', 'param']:
        key = 'passwd' if k == 'pass' else k
        if k not in ret and key in kw:
            ret[k] = kw[key]
    return ret


def get_opts(spec = None, argv = None, **kw):
    panic  = kw.get('panic',  True)
    greedy = kw.get('greedy', True)
    if argv is None:
        argv = sys.argv[1:]
    if not spec:
        return ({}, argv)

    try:
        if greedy:
            (o, args) = getopt.gnu_getopt(argv, spec)
        else:
            (o, args) = getopt.getopt(argv, spec)
    except getopt.GetoptError as e:
        if panic:
            sys.stderr.write(f'{str(e)}\n')
            sys.exit(2)

    # make sure all switch chars are in opts, use None as False
    opts = {k: None if (k + ':') in spec else False
            for k in spec.replace(':', '')}
    for key, val in o:
        opts[key[1:2]] = val or True

    return (opts, args)


def parse_opts(spec = None, argv = None, **kw):
    panic  = kw.get('panic',  True)
    greedy = kw.get('greedy', True)
    argc   = kw.get('argc',   None) # die(help) on error
    app    = kw.get('app',    None) # used in die(help)
    if argv is None:
        argv = sys.argv[1:]
    if not spec:
        return ({}, argv)

    # parse spec for human to spec for getopt
    s_spec, l_spec, odict = parse_cmd_spec(spec)

    # parse with standard getopt
    o = {}
    args = []
    try:
        if greedy:
            (o, args) = getopt.gnu_getopt(argv, s_spec, l_spec)
        else:
            (o, args) = getopt.getopt(argv, s_spec, l_spec)
    except getopt.GetoptError as e:
        if panic:
            sys.stderr.write(f'{str(e)}\n')
            sys.exit(2)

    # check args count
    if argc is not None:
        if isinstance(argc, int):
            # argc = N
            good = len(args) == argc
        elif isinstance(argc, tuple):
            if len(argc) == 1:
                # argc = (N,)
                good = len(args) >= argc[0]
            else:
                # argc = (N,M)
                good = len(args) >= argc[0] and len(args) <= argc[1]
        else:
            good = True # ignore argc type error
        if not good:
            die_usage(spec, name = app)

    # fill default values from spec
    opts = OptDict({k: None if v else False for k, v in odict.items()})

    # fill values from command line
    for key, val in o:
        key = key[2:] if key[1] == '-' else key[1:]
        opts[key] = val if odict[key] else True

    return (opts, args)


class OptDict(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    # support x['a', 'b']
    def __getitem__(self, key):
        if isinstance(key, tuple):
            for x in key:
                if self.__dict__[x]:
                    return self.__dict__[x]
            return self.__dict__[key[-1]]
        return self.__dict__[key]
    def __delitem__(self, key):
        del self.__dict__[key]
    def __iter__(self):
        return iter(self.__dict__)
    def __len__(self):
        return len(self.__dict__)
    def __str__(self):
        return str(self.__dict__)
    def __repr__(self):
        return repr(self.__dict__)


def parse_cmd_spec(spec):
    s_spec, l_spec = ('', [])
    o_dict = {}
    for line in spec.split('\n'):
        line = line.strip()
        if len(line) < 2 or line[0] != '-':
            continue
        s_opt, l_opt = ('', '')
        # process short opt
        if line[1] != '-':
            s_opt = line[1]
            line = line[2:].strip()
        if line and line[0] == ',':
            line = line[1:].strip()
        mo = re.match(r'^--(\S+)(.*)$', line)
        if mo:
            l_opt = mo.group(1)
            line = mo.group(2)
        has_val = re.match('^<.+>', line.strip())
        if s_opt:
            o_dict[s_opt] = has_val
            s_spec += s_opt
            if has_val:
                s_spec += ':'
        if l_opt:
            o_dict[l_opt] = has_val
            if has_val:
                l_opt += '='
            l_spec.append(l_opt)
    return (s_spec, l_spec, o_dict)


### a4/__init__.py ends here
