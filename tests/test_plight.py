import pytest

# Test enabling
def test_default_nodestatus(status):
    assert status.get_node_state() == 'ENABLED'

def test_reset_state_enabled_from_disabled_nodestatus(status):
    status.set_node_state('disable')
    status.set_node_state('enable')
    assert status.get_node_state() == 'ENABLED'

def test_reset_state_enabled_from_offline_nodestatus(status):
    status.set_node_state('offline')
    status.set_node_state('enable')
    assert status.get_node_state() == 'ENABLED'

# Test disabling
def test_set_disabled_nodestatus(status):
    status.set_node_disabled()
    assert status.get_node_state() == 'DISABLED'

def test_set_state_disabled_nodestatus(status):
    status.set_node_state('disable')
    assert status.get_node_state() == 'DISABLED'

def test_reset_state_disabled_from_offline_nodestatus(status):
    status.set_node_state('offline')
    status.set_node_state('disable')
    assert status.get_node_state() == 'DISABLED'

# Test offline
def test_set_offline_nodestatus(status):
    status.set_node_offline()
    assert status.get_node_state() == 'OFFLINE'

def test_set_state_offline_nodestatus(status):
    status.set_node_state('offline')
    assert status.get_node_state() == 'OFFLINE'

def test_reset_state_offline_from_disabled_nodestatus(status):
    status.set_node_state('disable')
    status.set_node_state('offline')
    assert status.get_node_state() == 'OFFLINE'

