import os
import pytest
import warnings


def _setoption(wmod, arg):
    """
    Copy of the warning._setoption function but does not escape arguments.
    """
    parts = arg.split(':')
    if len(parts) > 5:
        raise wmod._OptionError("too many fields (max 5): %r" % (arg,))
    while len(parts) < 5:
        parts.append('')
    action, message, category, module, lineno = [s.strip()
                                                 for s in parts]
    action = wmod._getaction(action)
    category = wmod._getcategory(category)
    if lineno:
        try:
            lineno = int(lineno)
            if lineno < 0:
                raise ValueError
        except (ValueError, OverflowError):
            raise wmod._OptionError("invalid lineno %r" % (lineno,))
    else:
        lineno = 0
    wmod.filterwarnings(action, message, category, module, lineno)


def pytest_addoption(parser):
    group = parser.getgroup("pytest-warnings")
    group.addoption(
        '-W', '--pythonwarnings', action='append',
        help="set which warnings to report, see -W option of python itself.")
    parser.addini("filterwarnings", type="linelist",
                  help="Each line specifies warning filter pattern which would be passed"
                  "to warnings.filterwarnings. Process after -W and --pythonwarnings.")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    args = item.config.getoption('pythonwarnings') or []
    inifilters = item.config.getini("filterwarnings")
    with warnings.catch_warnings(record=True) as log:
        warnings.simplefilter('once')
        for arg in args:
            warnings._setoption(arg)

        for arg in inifilters:
            _setoption(warnings, arg)

        yield

    for warning in log:
        msg = warnings.formatwarning(
            warning.message, warning.category,
            os.path.relpath(warning.filename), warning.lineno, warning.line)
        fslocation = getattr(item, "location", None)
        if fslocation is None:
            fslocation = getattr(item, "fspath", None)
        else:
            fslocation = "%s:%s" % fslocation[:2]
        fslocation = "in %s the following warning was recorded:\n" % fslocation
        item.config.warn("W0", msg, fslocation=fslocation)
