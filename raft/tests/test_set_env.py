import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from env_config import set_env

def test_set_env():
    """
    Tests that the environment is set correctly and temporarily inside the context manager.
    """

    env = {
        'HOSTNAME': 'localhost',
        'OPENAI_API_KEY': '<key_1>',
    }

    os.environ.update(env)

    assert os.environ['OPENAI_API_KEY'] == '<key_1>'
    assert os.environ['HOSTNAME'] == 'localhost'
    assert 'UNSET' not in os.environ['HOSTNAME']
    with set_env(OPENAI_API_KEY = '<key_2>', UNSET = 'whatever'):
        assert os.environ['OPENAI_API_KEY'] == '<key_2>'
        assert os.environ['HOSTNAME'] == 'localhost'
        assert os.environ['UNSET'] == 'whatever'
    assert os.environ['OPENAI_API_KEY'] == '<key_1>'
    assert os.environ['HOSTNAME'] == 'localhost'
    assert 'UNSET' not in os.environ['HOSTNAME']
