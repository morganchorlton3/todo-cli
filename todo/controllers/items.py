from time import strftime

from cement import Controller, ex

class Items(Controller):
    class Meta:
        label = 'items'
        stacked_type = 'embedded'
        stacked_on = 'base'

    @ex(help='list items')
    def list(self):
        data = {}
        try:
            project = self.app.config.get('todo', 'todoist_selected_project')
            tasks = self.app.todoist.get_tasks(project_id=project)
            data['tasks'] = tasks

        except Exception as error:
            self.app.log.error(error)

        self.app.render(data, 'items/list.jinja2')

    @ex(
        help='create an item',
        arguments=[
            (['item_text'],
             {'help': 'todo item text',
              'action': 'store'})
        ],
    )
    def create(self):
        text = self.app.pargs.item_text
        try:
            task = self.app.todoist.add_task(
                content=text,
                priority=1,
            )
            self.app.log.info(task)
        except Exception as error:
            self.app.log.error(error)

    @ex(
        help='update an existing item',
        arguments=[
            (
                    ['item_id'],
                    {
                        'help': 'todo item database id',
                        'action': 'store'
                    }
            ),
            (
                    ['--text'],
                    {
                        'help': 'todo item text',
                        'action': 'store',
                        'dest': 'item_text'
                    }
            ),
        ],
    )
    def update(self):
        id = int(self.app.pargs.item_id)
        text = self.app.pargs.item_text
        now = strftime("%Y-%m-%d %H:%M:%S")
        self.app.log.info('updating todo item: %s - %s' % (id, text))

        item = {
            'timestamp': now,
            'text': text,
        }

        self.app.db.update(item, doc_ids=[id])

    @ex(
        help='delete an item',
        arguments=[
            (
                    ['item_id'],
                    {
                        'help': 'todo item database id',
                        'action': 'store'
                    }
            ),
        ],
    )
    def delete(self):
        id = int(self.app.pargs.item_id)
        self.app.log.info('deleting todo item id: %s' % id)
        self.app.db.remove(doc_ids=[id])

    @ex(
        help='complete an item',
        arguments=[
            (['item_id'],
             {'help': 'todo item database id',
              'action': 'store'}),
        ],
    )
    def complete(self):
        id = int(self.app.pargs.item_id)
        now = strftime("%Y-%m-%d %H:%M:%S")
        item = self.app.db.get(doc_id=id)
        item['timestamp'] = now
        item['state'] = 'complete'

        self.app.log.info('completing todo item: %s - %s' % (id, item['text']))
        self.app.db.update(item, doc_ids=[id])

        ### send an email message

        msg = """
            Congratulations! The following item has been completed:

            %s - %s
            """ % (id, item['text'])

        self.app.mail.send(msg,
                           subject='TODO Item Complete',
                           to=[self.app.config.get('todo', 'email')],
                           from_addr='noreply@localhost',
                           )
