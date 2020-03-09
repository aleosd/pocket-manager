import datetime

import peewee

from . import const


db = peewee.SqliteDatabase(str(const.DATABASE_PATH))


class LinkInfo(peewee.Model):
    STATUS_UNREAD = 0
    STATUS_ARCHIVED = 1
    STATUS_DELETED = 2

    id = peewee.IntegerField(unique=True, index=True)
    given_title = peewee.CharField(null=True)
    resolved_title = peewee.CharField(null=True)
    given_url = peewee.CharField(null=True)
    resolved_url = peewee.CharField(null=True)
    excerpt = peewee.TextField(null=True)
    status = peewee.IntegerField(null=True)
    created_at = peewee.DateTimeField(null=True)

    last_check = peewee.DateTimeField(null=True)
    check_result = peewee.IntegerField(null=True)

    class Meta:
        database = db

    def update_check_result(self, new_status_code):
        self.last_check = datetime.datetime.now()
        if self.check_result != new_status_code:
            self.check_result = new_status_code
        self.save()


def add_link(link_data: dict):
    defaults = {
        'given_title': link_data.get('given_title'),
        'resolved_title': link_data.get('resolved_title'),
        'given_url': link_data.get('given_url'),
        'resolved_url': link_data.get('resolved_url'),
        'excerpt': link_data.get('excerpt'),
        'status': int(link_data.get('status')),
    }
    created_at = link_data.get('time_added')
    if created_at:
        defaults.update({
            'created_at': datetime.datetime.fromtimestamp(int(created_at)),
        })
    new_link, created = LinkInfo.get_or_create(
        id=link_data['item_id'], defaults=defaults
    )
    if not created:
        LinkInfo.update(**defaults).where(LinkInfo.id == new_link.id).execute()
    else:
        new_link.save()
    return new_link, created


def delete_link(link_id: int):
    record = LinkInfo.get(LinkInfo.id == link_id)
    record.delete_instance()


def remove_deleted():
    query = LinkInfo.delete().where(LinkInfo.status == LinkInfo.STATUS_DELETED)
    return query.execute()


def init():
    db.connect()
    db.create_table(LinkInfo)


def stat():
    return {
        'total': LinkInfo.select().count(),
        'unread': LinkInfo.select().where(
            LinkInfo.status == LinkInfo.STATUS_UNREAD).count(),
        'archived': LinkInfo.select().where(
            LinkInfo.status == LinkInfo.STATUS_ARCHIVED).count(),
    }


def get_records():
    return LinkInfo.select().order_by(LinkInfo.created_at)
