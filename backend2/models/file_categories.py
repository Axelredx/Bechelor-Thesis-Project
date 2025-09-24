from mongoengine import Document, StringField

class FileCategory(Document):
    file_category_string = StringField(required=True)
    full_file_category_and_descr_string = StringField(required=True)

    meta = {
        'collection': 'file_categories',
        'indexes': ['full_file_category_and_descr_string']
    }