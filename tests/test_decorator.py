import pytest
from owl.decorator import node, workflow, get_registered_nodes, llm_node
from owl.types import NodeInputType
from owl.node import BaseNode, LlmNode


def test_node_decorator_and_registry():
    @node(
        name='test',
        input_types=NodeInputType(required={'m':int}),
        output_types=NodeInputType(required={'n':int})
    )
    def fn(m):
        return {'n': m*2}

    reg = get_registered_nodes()
    node_obj = reg['test']
    assert isinstance(node_obj, BaseNode)
    assert 'test' in reg
    out = reg['test'].run({'m':3})
    assert out['n']==6


def test_workflow_decorator_validation():
    from owl.node import BaseNode

    @node(
        name='n1',
        input_types=NodeInputType(required={'a':int}),
        output_types=NodeInputType(required={'b':int})
    )
    def n1(a): return {'b':a}
    assert isinstance(n1, BaseNode)

    @node(
        name='n2',
        input_types=NodeInputType(required={'c':int}),
        output_types=NodeInputType(required={'d':int})
    )
    def n2(c): return {'d':c}
    assert isinstance(n2, BaseNode)

    @workflow('wf_test')
    def build(wf):
        wf.add_node(n1).add_node(n2)
    # Should raise orphans for n1 and n2
    with pytest.raises(Exception):
        build()


def test_llm_node_decorator_and_registry():
    @llm_node(
        name='test_llm',
        input_types=NodeInputType(required={'prompt': str}),
        output_types=NodeInputType(required={'output': str}),
        provider='openai',
        model_name='gpt-4'
    )
    def fn(prompt):
        # Dummy function; LlmNode uses its own run logic
        return {'output': 'ignored'}

    reg = get_registered_nodes()
    node_obj = reg['test_llm']
    assert isinstance(node_obj, LlmNode)
    assert 'test_llm' in reg
