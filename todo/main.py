import os

from cement import App, TestApp, init_defaults
from cement.core.exc import CaughtSignal
from cement.utils import fs, shell
from todoist_api_python.api import TodoistAPI

from .controllers.base import Base
from .controllers.items import Items
from .core.exc import TodoError

# configuration defaults
CONFIG = init_defaults('todo')
CONFIG['todo']['todoist_api_key_path'] = '~/.todo/key.txt'
CONFIG['todo']['todoist_selected_project_path'] = '~/.todo/selected_project.txt'
CONFIG['todo']['todoist_selected_project'] = None


def collect_api_key(key_file: str) -> str:
    p = shell.Prompt("Please enter your Todoist API key: ")
    key = p.prompt()
    f = open(key_file, "a")
    f.truncate(0)
    f.write(key)
    f.close()
    return key


def setup_project(app, projects):
    project_file = app.config.get('todo', 'todoist_selected_project_path')
    project_file = fs.abspath(project_file)
    if os.path.isfile(project_file):
        f = open(project_file, "r")
        project = f.read()
        f.close()
    else:
        projects_map  = {}
        for project in projects:
            projects_map[project.name] = project.id

        p = shell.Prompt(
            "Which project would you like to use?",
            options=list(projects_map.keys()),
            numbered=True
        )
        project = p.prompt()
        project = projects_map[project]

        f = open(project_file, "a")
        f.truncate(0)
        f.write(project)
        f.close()

    app.config.set('todo', 'todoist_selected_project', project)


def setup_todoist(app):
    key_file = app.config.get('todo', 'todoist_api_key_path')

    # ensure that we expand the full path
    key_file = fs.abspath(key_file)

    if os.path.isfile(key_file):
        f = open(key_file, "r")
        key = f.read()
        f.close()
    else:
        key = collect_api_key(key_file)

    authenticated = False
    while not authenticated:
        api = TodoistAPI(key)
        try:
            projects = api.get_projects()
            authenticated = True
            app.extend('todoist', api)
            project = app.config.get('todo', 'todoist_selected_project')
            if project is None:
                setup_project(app, projects)

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
            ('post_setup', setup_todoist),
        ]


class TodoTest(TestApp, Todo):
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
