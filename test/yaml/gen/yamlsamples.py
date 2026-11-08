import yaml, glob, os, sys
sys.path.insert(0, os.path.dirname(__file__))
src = open(os.path.join(os.path.dirname(__file__), 'yamlcases.py')).read()
ns = {'yaml': yaml, 'json': __import__('json'), 'math': __import__('math')}
exec(src[src.index('def canon'):src.index('out = []')], ns)
home = os.path.expanduser('~')
files = sorted(glob.glob('test/fixtures/mulet-samples/**/*.yaml', recursive=True))
print('(ns yaml-samples-test (:require [mulay.lib.yaml :as y] [clay.string :as str] [clay.io :as io]))')
print(open(sys.argv[1]).read())
print('(defn canon-file Str [rel: Str] (let [[src err] (read-file rel)] (if (= err "") (canon-doc src) (str "IOERR " err))))')
print('(deftest mulet-sample-yaml')
for f in files:
    exp = ns['canon'](yaml.load(open(f).read(), Loader=ns['L']))
    rel = f
    print('  (is (= (canon-file %s) %s))' % (ns['cstr'](rel), ns['cstr'](exp)))
print('  (is true))')
