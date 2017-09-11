import plight
import plight.util as util

def test_format_list_states(capsys, states):
    check = ''
    for state, details in states.items():
        if details['file'] is None:
            message_modifier = ' [default]'
        else:
            message_modifier = ''
        check += 'State: {0}{1}\nCode: {2}\nMessage: {3}\n\n'.format(
            state, message_modifier, details['code'], details['message'])

    util.format_list_states('enabled', states)
    out, err = capsys.readouterr()
    assert out == check

def test_running_format_get_current_state(capsys, states, pidfile):
    if not pidfile.is_locked():
        pidfile.acquire()
    check = ''
    for state, details in states.items():
        message = 'State: {0}\nCode: {1}\nMessage: {2}\n'
        check = message.format(state, details['code'], details['message'])
        util.format_get_current_state(state, details)
        out, err = capsys.readouterr()
        assert out == check
    if pidfile.is_locked():
        pidfile.release()

def test_stopped_format_get_current_state(capsys, states, pidfile):
    if pidfile.is_locked():
        pidfile.release()
    check = ''
    for state, details in states.items():
        warning = 'WARNING: plight is not running\n'
        message = '{0}State: {1}\nCode: {2}\nMessage: {3}\n'
        check = message.format(
                    warning, state, details['code'], details['message'])
        util.format_get_current_state(state, details)
        out, err = capsys.readouterr()
        assert out == check
