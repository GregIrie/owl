import pytest
from owl.workflow import Workflow
from owl.node import BaseNode
from owl.types import NodeInputType
from owl.errors import NodeConnectionError


def make_node(name, in_key, out_key):
    return BaseNode(
        name=name,
        input_types=NodeInputType(required={in_key: int}),
        output_types=NodeInputType(required={out_key: int}),
        run_fn=lambda **inputs: {out_key: inputs[in_key] + 1}
    )


def test_workflow_add_and_connect_and_run():
    a = make_node('a', 'x', 'y')
    b = make_node('b', 'y', 'z')
    wf = Workflow('wf')
    wf.add_node(a).add_node(b).connect(a, b)
    res = wf.run({'x': 1})
    assert res['y'] == 2
    assert res['z'] == 3


def test_workflow_cycle_detection():
    a = make_node('a', 'x', 'y')
    b = make_node('b', 'y', 'x')
    wf = Workflow('cycle')
    wf.add_node(a).add_node(b)
    wf.connect(a, b)
    wf.connect(b, a)
    with pytest.raises(NodeConnectionError):
        wf.run({'x': 0})
