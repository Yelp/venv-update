def exec_file(fname, lnames=None, gnames=None):
    """a python3 replacement for execfile"""
    with open(fname) as f:
        code = compile(f.read(), fname, 'exec')
        exec(code, lnames, gnames)  # pylint:disable=exec-used
