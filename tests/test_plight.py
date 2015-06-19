import pytest

def test_default_nodestatus(status, states):
    """
    There are only two default states defined in the
    test cases. This looks for them explicitly
    and asserts if neither is found.
    """
    found = False
    for default in ['enabled', 'master']:
        if default in states.keys():
            assert status.get_node_state() == default.upper()
            found = True
    assert found

def test_default_nodestatus_details(status, states):
    """
    Ensure that the NodeStatus object maintains data to match
    the provided states
    """
    if status._default_state in states.keys():
        for (state, data) in states.items():
            for (detail, value) in data.items():
                assert status.get_state_detail(detail, state) == value
                if state == 'master' and detail == 'message':
                    assert status.get_state_detail(detail, state) == 'master node'

def test_change_nodestatus(status, states):
    """
    Loop through every state and ensure that it is changed
    to successfully
    """
    for (state, data) in states.items():
        status.set_node_state(data['command'])
        assert status.get_node_state() == state.upper()

def test_reset_state_to_default_nodestatus(status, states):
    """
    Loop though every state, then reset to the default state
    and verify it behaved as expected
    """
    found = False
    for (state, data) in states.items():
        status.set_node_state(data['command'])
        if status._default_state in ['enabled', 'master']:
            status.set_node_state(status._default_state)
            assert status.get_node_state() == status._default_state.upper()
            found = True
    assert found