#!/usr/bin/env python3

from string import ascii_lowercase, ascii_uppercase
from itertools import chain, product, count, tee, islice, repeat
from subprocess import check_call, CalledProcessError
from tempfile import mkdtemp
from pathlib import Path
from argparse import ArgumentParser
from logging import getLogger, DEBUG, basicConfig

logger = getLogger(__name__)
basicConfig(level=DEBUG)

nwise = lambda g, n=2: zip(*(islice(g, i, None) for i, g in enumerate(tee(g, n))))
first = lambda g, n=1: zip(chain(repeat(True, n), repeat(False)), g)

KEYWORDS = {
    'abstract', 'assert'      , 'boolean' , 'break'     ,
    'byte'    , 'case'        , 'catch'   , 'char'      ,
    'class'   , 'const'       , 'continue', 'default'   ,
    'do'      , 'double'      , 'else'    , 'enum'      ,
    'extends' , 'final'       , 'finally' , 'float'     ,
    'for'     , 'goto'        , 'if'      , 'implements',
    'import'  , 'instanceof'  , 'int'     , 'interface' ,
    'long'    , 'native'      , 'new'     , 'package'   ,
    'private' , 'protected'   , 'public'  , 'return'    ,
    'short'   , 'static'      , 'strictfp', 'super'     ,
    'switch'  , 'synchronized', 'this'    , 'throw'     ,
    'throws'  , 'transient'   , 'try'     , 'void'      ,
    'volatile', 'while'       , 'true'    , 'false'     ,
    'null'    ,
}
names = lambda src: (''.join(x) for x in chain.from_iterable(product(src, repeat=n) for n in count(1)))
valid_names = lambda src: (n for n in names(src) if n not in KEYWORDS)

java_code = lambda params: '''
public class Test {{
    public <{params}> void testMethod() {{}}
}}
'''.format(params=', '.join(params))

def java_code_extends(params):
    params = (y if is_first else f'{y} extends {x}' for is_first, (x, y) in first(nwise(params)))
    return java_code(params)

def search(path, code_func, names, bounds):
    logger.debug('Searching @ %r', bounds)
    if bounds.stop - bounds.start <= 1:
        return bounds.start
    filename = path / 'Test.java'
    idx = (bounds.stop + bounds.start) // 2
    with open(filename, 'w') as f:
        f.write(code_func(names[:idx]))
    try:
        rv = check_call(['javac', filename])
        return search(path, code_func, names, range(idx, bounds.stop))
    except CalledProcessError:
        return search(path, code_func, names, range(bounds.start, idx))

parser = ArgumentParser()
parser.add_argument('-p', '--path', type=Path)
parser.add_argument('-m', '--max', type=int, default=10_000)
parser.add_argument('-s', '--src', type=str)

if __name__ == "__main__":
    args = parser.parse_args()
    path = Path(mkdtemp()) if args.path is None else args.path
    bounds = range(0, args.max)
    src = ascii_uppercase + ascii_lowercase if args.src is None else args.src

    logger.debug('Path = %r', path)
    rv = search(path, java_code_extends, list(islice(valid_names(src), bounds.stop)), bounds)
    logger.info('Found maximum number of arguments %s', rv)
    logger.info('File at <%s>', path)
    with open(path / 'Test.java') as f:
        for line in f:
            logger.info('> %s', line.rstrip('\n'))
