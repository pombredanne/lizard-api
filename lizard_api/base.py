

import logging

from django.contrib.gis.db import models
from django.contrib.gis.geos.io import WKTReader
from django.db.models.fields import FieldDoesNotExist
from djangorestframework.views import View

import json

logger = logging.getLogger(__name__)


class BaseApiView(View):
    """
        Base class for api's with possibilities for quering, pagination, get,
        create, update and delete and base functions for working with related
        objects (one2many, many2many and many2many tables through another table

        integrates well with the Ext-js interfaces developed in the KRW-vss
        project.
        <<todo: add documentations which classes>>

        related fields:
        always a representation with id and name
    """

    #predefined sizes of return (all fields or just a selection)
    SMALL = 1
    MEDIUM = 2
    COMPLETE = 3
    ID_NAME = 0

    size_dict = {
        'id_name': ID_NAME,
        'small': SMALL,
        'medium': MEDIUM,
        'complete': COMPLETE
    }

    model_class = None

    #boolean field which marks if field is deleted
    valid_field = None
    valid_value = True

    name_field = 'name'

    #slug field support. use object_slug instead of object_id to query on slug
    slug_field = None

    read_only = None
    ######## specific functions #######

    use_filtered_model = False

    def get_object_for_api(self,
                           measure,
                           flat=True,
                           size=COMPLETE,
                           include_geom=False):
        pass

    def update_many2many(self, record, model_field, linked_records):
        pass

    def update_one2many(record, key, value):
        pass

    ####### base get object #######

    def get(self, request):
        """
            returns object or list of objects

        """
        object_id = self._str2int_or_none(request.GET.get('object_id', None))
        object_slug = request.GET.get('object_slug', None)
        size = request.GET.get('size', 'complete')
        flat = self._str2bool_or_none(request.GET.get('flat', False))
        include_geom = self._str2bool_or_none(
            request.GET.get('include_geom', True))
        show_deleted = self._str2bool_or_none(
            request.GET.get('show_deleted', False))
        filter = request.GET.get('filter', None)

        size = self.size_dict[size.lower()]

        model = self.model_class

        logger.debug("""input for api is:
                object_id: %s
                size: %s
                include_geom; %s
                flat: %s
              """ % (str(object_id), str(size), str(include_geom), str(flat)))

        if object_id is not None or object_slug is not None:
            #return single object
            if object_id is not None:
                obj = model.objects.get(id=object_id)
            else:
                obj = model.objects.get(slug=object_slug)

            output = self.get_object_for_api(
                obj, flat=flat, size=size, include_geom=include_geom)
            return {'success': True, 'data': output}

        else:
            #return list with objects
            start = int(request.GET.get('start', 0))
            limit = int(request.GET.get('limit', 25))
            query = request.GET.get('query', None)
            sort = request.GET.get('sort', None)

            output = []

            if self.use_filtered_model:
                objs = self.get_filtered_model(request)
            else:
                objs = model.objects.all()

            if not show_deleted and self.valid_field:
                objs = objs.filter(**{self.valid_field: self.valid_value})

            if query:
                for q in query.split(','):
                    q = q.split(':')
                    a = len(q)
                    if len(q) == 1:
                        #only filter and not field given, take name field
                        q = [self.name_field, q[0]]
                    if q[1] == 'None':
                        q[1] = None
                    q[0] = q[0] + '__istartswith'
                    objs = objs.filter(**{q[0]: q[1]})

            if filter:
                filter = json.loads(filter)
                for f in filter:
                    if f['property'] in self.field_mapping:
                        objs = objs.filter(
                            **{self.field_mapping[f['property']]: f['value']})
                    else:
                        logger.debug(
                            'field %s is not filterable', f['property'])
            if sort:
                sort_params = self.transform_sort_params(sort)
                objs = objs.order_by(*sort_params)

            for obj in objs[start:(start + limit)]:
                obj_instance = self.get_object_for_api(
                    obj, flat=flat, size=size, include_geom=include_geom)
                #if obj_instance is not None:
                output.append(obj_instance)
            return {'success': True,
                    'data': output,
                    'count': objs.count(),
                    'total': objs.count()}

    def transform_sort_params(self, sort_input):
        """
            transforms sort request of Ext.store to django input for sort_by
        """
        output = []
        for inp in json.loads(sort_input):
            if inp['property'] in self.field_mapping:
                model_param = self.field_mapping[inp['property']]
                if inp['direction'] == 'ASC':
                    model_param = '-' + model_param
                output.append(model_param)
        return output

    #########functions around a post (update, create, delete) ########

    def proceed_action(self, action, data):
        """
            Update, create or delete records

        """
        touched_objects = None

        if action == 'delete':  # OK
            success = self.delete_objects(data)
        elif action == 'create':
            success, touched_objects = self.create_objects(data)
        elif action == 'update':
            success, touched_objects = self.update_objects(data)
        else:
            logger.error("Unkown post action '%s'." % action)
            success = False

        return success, touched_objects

    def touched_object_to_dict(self, touched_objects, flat, size,
                               include_geom, return_dict):
        output = []
        if touched_objects:
            for obj in touched_objects:
                touched_dict = self.get_object_for_api(
                    obj, flat=flat, size=size, include_geom=include_geom)
                output.append(touched_dict)

            if return_dict:
                # just return single object
                output = output[0]
        return output

    def post(self, request):
        #request params
        action = request.GET.get('action', None)
        size = request.GET.get('size', 'complete')
        flat = self._str2bool_or_none(request.GET.get('flat', False))
        include_geom = self._str2bool_or_none(
            request.GET.get('include_geom', True))
        data = json.loads(self.CONTENT.get('data', []))
        edit_message = self.CONTENT.get('edit_message', None)

        size = self.size_dict[size.lower()]
        return_dict = False

        logger.debug("""input for api is:
                action: %s
                data: %s
                edit_message: %s
              """ % (str(action), str(data), str(edit_message)))

        if type(data) == dict:
            # get single object and return single object
            return_dict = True
            data = [data]

        success, touched_objects = self.proceed_action(action, data)
        output = self.touched_object_to_dict(
            touched_objects, flat, size, include_geom, return_dict)
        return {'success': success,
                'data': output}

    def create_objects(self, data):
        """
            create records

            issues(todo):
            - everything in one database transaction
        """
        # Read only fields *could* be defined on view inheriting
        # from this class.
        if not hasattr(self, 'read_only_fields'):
            self.read_only_fields = []

        touched_objects = []
        model = self.model_class

        success = True

        for item in data:
            record = model()
            if 'edit_summary' in item:
                lizard_history_summary = item.pop('edit_summary')
                record.lizard_history_summary = lizard_history_summary
            touched_objects.append(record)

            # Loop all fields. Value of a field can also be a list.
            for (key, value) in item.items():
                key = str(key)
                set_value = True

                if not key in self.read_only_fields:
                    try:
                        model_field = model._meta.get_field(key)

                        if model_field.rel is not None and type(model_field.rel) == models.ManyToManyRel:
                            pass
                        elif key == 'id':
                            pass
                        else:
                            if type(model_field.rel) == models.ManyToOneRel:
                                #input is a dictionary with an id and name in json
                                if value is None or value == {} or value == [] or value == '':
                                    value = None
                                    set_value = False
                                else:
                                    if type(value) == list:
                                        value = value[0]
                                    value = model_field.rel.to.objects.get(pk=value['id'])

                            elif type(model_field) == models.IntegerField and len(model_field._get_choices()) > 0:
                                #input is a dictionary with an id and name in json
                                if value is None or value == {} or value == [] or value == '':
                                    value = None
                                    set_value = False
                                else:
                                    if type(value) == list:
                                        value = value[0]
                                    value = value

                            elif isinstance(model_field, models.IntegerField):
                                value = self._str2int_or_none(value)

                            elif isinstance(model_field, models.FloatField):
                                value = self._str2float_or_none(value)

                            elif isinstance(model_field, models.BooleanField):
                                value = self._str2bool_or_none(value)

                            elif isinstance(model_field, models.GeometryField):
                                if value is None or value == '':
                                    value = None
                                else:
                                    reader = WKTReader()
                                    value = reader.read(value)

                            if set_value:
                                setattr(record, key, value)

                    except FieldDoesNotExist:
                        logger.error(
                            "Field %s.%s not exists." % (model._meta.module_name, key))
                        success = False
                        Exception('field error')

            record.save()

            for (key, value) in item.items():
                key = str(key)
                if not key in self.read_only_fields:

                    try:
                        model_field = model._meta.get_field(key)

                        if model_field.rel is not None and type(model_field.rel) == models.ManyToManyRel:
                            self.update_many2many(record, model_field, value)

                    except FieldDoesNotExist:
                        logger.error(
                            "Field %s.%s not exists." % (model._meta.module_name, key))
                        success = False
                        Exception('field error')

        return success, touched_objects

    def update_objects(self, data):
        """
            Update records

            issues(todo):
            - everything in one database transaction
        """
        # Read only fields *could* be defined on view inheriting
        # from this class.
        if not hasattr(self, 'read_only_fields'):
            self.read_only_fields = []

        touched_objects = []
        model = self.model_class
        success = True

        for item in data:
            record = model.objects.get(pk=item['id'])
            if 'edit_summary' in item:
                lizard_history_summary = item.pop('edit_summary')
                record.lizard_history_summary = lizard_history_summary
            touched_objects.append(record)

            for (key, value) in item.items():
                key = str(key)
                set_value = True
                if not key in self.read_only_fields:
                    try:
                        one2many_rel = False
                        try:
                            model_field = model._meta.get_field(key)
                            name = model_field.name
                        except FieldDoesNotExist:
                            if getattr(record, key):
                                model_field = None
                                one2many_rel = True
                                name = key

                        if one2many_rel:
                            self.update_one2many(record, key, value)
                        elif  model_field.rel is not None and type(model_field.rel) == models.ManyToManyRel:
                            self.update_many2many(record, model_field, value)
                        else:
                            if type(model_field.rel) == models.ManyToOneRel:
                                #input is a dictionary with an id and name in json
                                if value is None or value == {} or value == [] or value == ['']:
                                    value = None
                                    #set_value = False
                                else:
                                    if type(value) == list:
                                        value = value[0]
                                    value = model_field.rel.to.objects.get(pk=value['id'])

                            if type(model_field) == models.IntegerField and len(model_field._get_choices()) > 0:
                                #input is a dictionary with an id and name in json
                                if value is None or value == {} or value == []:
                                    value = None
                                    set_value = False
                                else:
                                    if type(value) == list:
                                        value = value[0]
                                    value = value['id']

                            if isinstance(model_field, models.IntegerField):
                                value = self._str2int_or_none(value)

                            if isinstance(model_field, models.FloatField):
                                value = self._str2float_or_none(value)

                            if isinstance(model_field, models.BooleanField):
                                value = self._str2bool_or_none(value)

                            if isinstance(model_field, models.GeometryField):
                                if value is None or value == '':
                                    value = None
                                else:
                                    reader = WKTReader()
                                    value = reader.read(value)

                            if set_value:
                                setattr(record, key, value)

                    except (FieldDoesNotExist, AttributeError):
                        logger.error(
                            "Field %s.%s not exists." % (model._meta.module_name, key))
                        success = False
                        Exception('field error')
            record.save()
        return success, touched_objects

    def delete_objects(self, data):
        """Deactivate measure objects."""
        success = True
        model = self.model_class

        try:
            for record in data:
                object_id = record['id']
                object = model.objects.get(
                    pk=object_id)
                if self.valid_field:
                    setattr(object, self.valid_field, not self.valid_value)
                    object.save()
                else:
                    object.delete()
        except model.DoesNotExist:
                success = False
        return success

    #########base functions for working with related objects########

    def _get_related_objects(self, related_objects, flat=True):
        """
            get related objects (many2many field) as [{id:<> ,name:<>},{..}] or []
        """
        output = []
        for obj in related_objects.all():
            output.append(self._get_related_object(obj, flat))

        return output

    def _get_related_object(self, related_object, flat=True):
        """
            get related object as {id:<> ,name:<>} or None of None
        """
        if related_object is None:
            return None
        else:
            if flat:
                return str(related_object)
            else:
                return {'id': related_object.id, 'name': str(related_object)}

    def _get_choice(self, field, value, flat=True):
        """
            get related object as {id:<> ,name:<>} or None of None
        """
        if value is None:
            return None
        else:
            choices = dict(field._get_choices())

            if flat:
                return str(choices[value])
            else:
                return {'id': value, 'name': str(choices[value])}

    def save_single_many2many_relation(self, record, model_field, linked_records):
        """
            update specific part of manyToMany relations.
            input:
                - record: measure
                - model_field. many2many field object
                - linked_records. list with dictionaries with:
                    id: id of related objects
                    optional some relations in case the relation
                    is through another object
        """

        model_link = getattr(record, model_field.name)
        existing_links = dict([(obj.id, obj) for obj in model_link.all()])
        for linked_record in linked_records:

            if linked_record['id'] in existing_links.keys():
                #delete link from the list 'existing_links'
                del existing_links[linked_record['id']]
            else:
                #create new
                model_link.add(
                    model_field.rel.to.objects.get(pk=linked_record['id']))

        #remove existing links, that are not anymore
        for link in existing_links.itervalues():
            model_link.remove(link)

    #########base functions for transforming input to correct value########
    def _str2float_or_none(self, value):
        """
            returns integer of value, or when not a number returns 'None'
            in case of an object, takes id as value for evaluation
        """
        if type(value) == object and 'id' in value:
            value = value['id']

        try:
            return float(value)
        except (TypeError, ValueError):
            logger.error('value %s is not a float' % str(value))
            return None

    def _str2int_or_none(self, value):
        """
            returns integer of value, or when not a number returns 'None'
            in case of an object, takes id as value for evaluation
        """
        if type(value) == object and 'id' in value:
            value = value['id']

        try:
            return int(value)
        except (TypeError, ValueError):
            logger.error('value %s is not an integer' % str(value))
            return None

    def _str2bool_or_none(self, value):
        """
            returns integer of value, or when not a number returns 'None'
            in case of an object, takes id as value for evaluation
        """
        if type(value) == dict and 'id' in value:
            value = value['id']

        if type(value) == bool:
            return value
        elif type(value) in (str, unicode):
            if value.lower() in ('true', '1', 'on'):
                return True
            elif value.lower() in ('false', '0', 'off'):
                return False
            else:
                return None
        elif type(value) in (int, float):
            return bool(value)
        else:
            return None
