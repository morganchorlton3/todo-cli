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
        data['items'] = self.app.db.all()
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
        now = strftime("%Y-%m-%d %H:%M:%S")
        self.app.log.info('creating todo item: %s' % text)

        item = {
            'timestamp': now,
            'state': 'pending',
            'text': text,
        }

        self.app.db.insert(item)

    @ex(
        help='update an existing item',
        arguments=[
            (['item_id'],
             {'help': 'todo item database id',
              'action': 'store'}),
            (['--text'],
             {'help': 'todo item text',
              'action': 'store',
              'dest': 'item_text'}),
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


    @ex(help='delete an item')
    def delete(self):
        pass

    @ex(help='complete an item')
    def complete(self):
        pass
