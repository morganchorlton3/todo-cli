import os

from cement import App, TestApp, init_defaults
from cement.core.exc import CaughtSignal
from cement.utils import fs, shell

from .controllers.items import Items
from .core.exc import TodoError
from .controllers.base import Base

from todoist_api_python.api import TodoistAPI


# configuration defaults
CONFIG = init_defaults('todo')
CONFIG['todo']['todoist_api_key_path'] = '~/.todo/key.txt'

def collect_api_key(key_file: str) -> str:
    p = shell.Prompt("Please enter your Todoist API key: ")
    key = p.prompt()
    f = open(key_file, "a")
    f.truncate(0)
    f.write(key)
    f.close()
    return key

def extend_tinydb(app):
    key_file = app.config.get('todo', 'todoist_api_key_path')

    # ensure that we expand the full path
    key_file = fs.abspath(key_file)

    if os.path.isfile(key_file):
        f = open(key_file, "r")
        key = f.read()
    else:
        key = collect_api_key(key_file)

    authenticated = False
    while not authenticated:
        app.log.info(key)
        api = TodoistAPI(key)
        try:
            projects = api.get_projects()
            app.log.info(projects)
            authenticated = True
            app.extend('todoist', api)
        except Exception as error:
            app.log.error(error)
            key = collect_api_key(key_file)


class Todo(App):
    """Todo CLI primary application."""

    class Meta:
        label = 'todo'

        # configuration defaults
        config_defaults = CONFIG

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'yaml',
            'colorlog',
            'jinja2',
        ]

        # configuration handler
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # set the output handler
        output_handler = 'jinja2'

        # register handlers
        handlers = [
            Base,
            Items
        ]

        hooks = [
            ('post_setup', extend_tinydb),
        ]


class TodoTest(TestApp,Todo):
    """A sub-class of Todo that is better suited for testing."""

    class Meta:
        label = 'todo'


def main():
    with Todo() as app:
        try:
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except TodoError as e:
            print('TodoError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
