from setuptools import setup

setup(
    name = 'donkeypart_game_controller',
    version = '1.0.0',
    author = 'Tasuku Hori',
    author_email = 'tasuku-hori@exa-corp.co.jp',
    url = 'https://github.com/coolerking/donkeypart_game_controller',
    install_requires = ['docopt', 'donkeypart_bluetooth_game_controller', 'time', 'evdev'],
    extras_require = {
        'check_js': ['fcntl', 'strict']
    }
)
