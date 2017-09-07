def test_get_config(config):
    assert config
    assert config['host'] == '0.0.0.0'
    assert config['port'] == 10101
    assert config['web_log_file'] == '/var/log/plight/access.log'
    assert config['log_file'] == '/var/log/plight/plight.log'
    if 'enabled' in config['states']:
        state = config['states']['enabled']
        assert state['file'] == None
        assert state['code'] == 200
        assert state['priority'] == 0

    if 'disabled' in config['states']:
        state = config['states']['disabled']
        assert state['file'] == '/var/tmp/node_disabled'
        if 'old_config' in state and state['old_config']:
            assert state['code'] == 404
        else:
            assert state['code'] == 200
        assert state['command'] == 'disable'
        assert state['priority'] == 1

    if 'offline' in config['states']:
        state = config['states']['offline']
        assert state['file'] == '/var/tmp/node_offline'
        assert state['code'] == 200
        assert state['priority'] == 2

    if 'master' in config['states']:
        state = config['states']['master']
        assert state['file'] == None
        assert state['code'] == 200
        assert state['priority'] == 0

    if 'slave' in config['states']:
        state = config['states']['slave']
        assert state['file'] == '/var/tmp/node_slave'
        assert state['code'] == 200
        assert state['priority'] == 1
