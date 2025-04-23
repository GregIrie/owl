import pytest
from owl.types import NodeInputType
from owl.errors import NodeValidationError


def test_node_input_type_keys_and_uniqueness():
    nit = NodeInputType(required={'a': int}, optional={'b': str})
    assert nit.keys() == {'a', 'b'}
    assert nit.keys(include_optional=False) == {'a'}
    assert nit.keys(include_required=False) == {'b'}

    with pytest.raises(ValueError):
        NodeInputType(required={'x': int}, optional={'x': int})


def test_add_and_remove_input():
    nit = NodeInputType()
    nit.add_input('c', float, required=False)
    assert nit.keys() == {'c'}
    nit.remove_input('c')
    assert nit.keys() == set()
    with pytest.raises(KeyError):
        nit.remove_input('c')


def test_validate_success_and_failure():
    nit = NodeInputType(required={'a': int}, optional={'b': str})
    # Successful
    nit.validate({'a': 1, 'b': 'x'})
    # Missing required
    with pytest.raises(NodeValidationError):
        nit.validate({'b': 'x'})
    # Wrong type
    with pytest.raises(NodeValidationError):
        nit.validate({'a': 'not int'})
