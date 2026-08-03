from django.db.models.signals import class_prepared

def add_db_prefix(sender, **kwargs):
    if not sender._meta.db_table.startswith('doccure_'):
        sender._meta.db_table = 'doccure_' + sender._meta.db_table

class_prepared.connect(add_db_prefix)
