import time

import pytest

from command_line_client import CommandLineClient


@pytest.fixture
def cmd_client():
    client = CommandLineClient('plight')
    return client


@pytest.mark.parametrize('new_state', ['enable', 'disable', 'offline'])
def test_change_state(cmd_client, new_state):
    response = cmd_client.run_command(new_state)
    assert response.return_code == 0
    response = cmd_client.run_command('status')
    assert response.return_code == 0
    assert 'State: {state}'.format(state=new_state) in response.standard_out


def test_list_states(cmd_client):
    response = cmd_client.run_command('list-states')
    assert response.return_code == 0


def test_stop_and_start_service(cmd_client):
    sudo_client = CommandLineClient('sudo plight')
    response = sudo_client.run_command('stop')
    assert response.return_code == 0

    response = cmd_client.run_command('status')
    assert 'WARNING: plight is not running' in response.standard_out

    response = sudo_client.run_command('start')
    assert response.return_code == 0
    time.sleep(30)
    response = cmd_client.run_command('status')
    assert 'WARNING: plight is not running' not in response.standard_out
