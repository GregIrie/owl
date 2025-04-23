import pytest
from owl.node import BaseNode
from owl.types import NodeInputType
from owl.errors import NodeValidationError, NodeConnectionError


def dummy_fn(x: int) -> dict:
    return {'y': x + 1}


@pytest.fixture
def node_a():
    return BaseNode(
        name='a',
        input_types=NodeInputType(required={'x': int}),
        output_types=NodeInputType(required={'y': int}),
        run_fn=dummy_fn
    )

@pytest.fixture
def node_b():
    return BaseNode(
        name='b',
        input_types=NodeInputType(required={'y': int}),
        output_types=NodeInputType(required={'z': int}),
        run_fn=lambda y: {'z': y * 2}
    )


def test_run_and_validate(node_a):
    out = node_a.run({'x': 5})
    assert out == {'y': 6}
    with pytest.raises(NodeValidationError):
        node_a.run({'x': 'wrong'})


def test_validate_connection_success_and_failure(node_a, node_b):
    # b expects y, which a produces
    node_b.validate_connection(node_a)
    # a expects x, b does not produce x
    with pytest.raises(NodeConnectionError):
        node_a.validate_connection(node_b)
