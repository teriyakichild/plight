import pytest
import plight

@pytest.fixture(scope='module')
def status(request):
    status = plight.NodeStatus()
    def reset():
         status.set_node_enabled()
    request.addfinalizer(reset)
    return status

def test_default_nodestatus(status):
    assert status.get_node_state() == 'ENABLED'

def test_set_disabled_nodestatus(status):
    status.set_node_disabled()
    assert status.get_node_state() == 'DISABLED'

def test_set_state_disabled_nodestatus(status):
    status.set_node_state('disable')
    assert status.get_node_state() == 'DISABLED'

def test_reset_state_enabled_nodestatus(status):
    status.set_node_state('disable')
    status.set_node_state('enable')
    assert status.get_node_state() == 'ENABLED'
