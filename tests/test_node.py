import pytest
from owl.node import BaseNode
from owl.types import NodeInputType
from owl.errors import NodeValidationError, NodeConnectionError, NodeExecutionError
from owl.node import LlmNode, get_client


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


def test_base_node_missing_run_fn():
    with pytest.raises(ValueError):
        BaseNode(
            name='c',
            input_types=NodeInputType(required={}),
            output_types=NodeInputType(required={}),
            run_fn=None
        )

class DummyClient:
    def __init__(self, response):
        self.response = response
    def generate(self, messages, **kwargs):
        return self.response

@pytest.fixture(autouse=True)
def patch_get_client(monkeypatch):
    def fake_get_client(provider, model_name):
        return DummyClient(response="generated text")
    monkeypatch.setattr('owl.node.get_client', fake_get_client)
    return fake_get_client

def test_llm_node_success():
    input_types = NodeInputType(required={'messages': list})
    output_types = NodeInputType(required={'reply': str})
    llm_node = LlmNode(
        name='llm',
        input_types=input_types,
        output_types=output_types,
        provider='test',
        model_name='model'
    )
    result = llm_node.run({'messages': ['hello']})
    assert result == {'reply': 'generated text'}

def test_llm_node_missing_messages():
    input_types = NodeInputType(required={'messages': list})
    output_types = NodeInputType(required={'reply': str})
    llm_node = LlmNode(
        name='llm',
        input_types=input_types,
        output_types=output_types,
        provider='test',
        model_name='model'
    )
    with pytest.raises(NodeValidationError):
        llm_node.run({})

def test_llm_node_execution_error(monkeypatch):
    class ErrorClient:
        def generate(self, messages, **kwargs):
            raise RuntimeError("fail")
    monkeypatch.setattr('owl.node.get_client', lambda p, m: ErrorClient())
    input_types = NodeInputType(required={'messages': list})
    output_types = NodeInputType(required={'reply': str})
    llm_node = LlmNode(
        name='llm',
        input_types=input_types,
        output_types=output_types,
        provider='test',
        model_name='model'
    )
    with pytest.raises(NodeExecutionError):
        llm_node.run({'messages': ['hello']})

def test_llm_node_multiple_output_keys():
    input_types = NodeInputType(required={'messages': list})
    output_types = NodeInputType(required={'a': str, 'b': str})
    with pytest.raises(ValueError):
        LlmNode(
            name='llm',
            input_types=input_types,
            output_types=output_types,
            provider='test',
            model_name='model'
        )
        