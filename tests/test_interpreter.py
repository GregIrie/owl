import pytest
from owl.interpreter import Interpreter, CodeExecutionError


def test_execute_simple():
    code = 'result = x + 1'
    interp = Interpreter(timeout=1)
    out = interp.execute(code, {'x': 5})
    assert out['result'] == 6


def test_forbidden_import():
    interp = Interpreter()
    with pytest.raises(CodeExecutionError):
        interp.execute('import os')


def test_timeout():
    interp = Interpreter(timeout=0.01)
    # Infinite loop
    with pytest.raises(CodeExecutionError):
        interp.execute('while True: pass')
