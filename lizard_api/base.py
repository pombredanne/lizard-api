

import logging

from django.contrib.gis.db import models
from django.contrib.gis.geos.io import WKTReader
from django.db.models.fields import FieldDoesNotExist
from djangorestframework.views import View

import json

logger = logging.getLogger(__name__)


class BaseApiView(View):
    """
        Base class for api's with possibilities for quering, pagination, get, create, update and delete and
        base functions for working with related objects (one2many, many2many and many2many tables through another table

        integrates well with the Ext-js interfaces developed in the KRW-vss project.
        <<todo: add documentations which classes>>



        related fields:
        always a representation with id and name


    """

    SMALL = 1
    MEDIUM = 2
    COMPLETE = 3

    size_dict = {
        'small': SMALL,
        'medium': MEDIUM,
        'complete': COMPLETE
    }

    model_class=None

    #boolean field which marks if field is deleted
    valid_field=None
    valid_value=True
    ######## specific functions #######


    def get_object_for_api(self, measure, flat=True, size=COMPLETE, include_geom=False):
        pass

    def update_many2many(self, record, model_field, linked_records):
        pass

#    def get_object_for_api(self, measure, flat=True, size=COMPLETE, include_geom=False):
#        """
#            create object of measure
#        """
#        output = {
#            'id':measure.id,
#            'ident': measure.ident,
#            'title': measure.title,
#            'is_KRW_measure': measure.is_KRW_measure,
#            'is_indicator': measure.is_indicator,
#            'description': measure.description,
#            'total_costs': measure.total_costs,
#            'investment_costs': measure.investment_costs,
#            'exploitation_costs': measure.exploitation_costs,
#            'responsible_department': measure.responsible_department,
#            'value': measure.value,
#            'measure_type': self._get_related_object(measure.measure_type, flat),
#            'period': self._get_related_object(measure.period, flat),
#            'unit': self._get_related_object(measure.unit, flat),
#            'categories': self._get_related_objects(measure.categories, flat),
#            'initiator': self._get_related_object(measure.initiator, flat),
#            'executive': self._get_related_object(measure.executive, flat),
#            'areas': self._get_related_objects(measure.areas, flat),
#            'waterbodies': self._get_related_objects(measure.waterbodies, flat),
#        }
#
#        if size >= self.MEDIUM:
#            output.update({
#                'aggregation_type':  self._get_choice(Measure._meta.get_field('aggregation_type'), measure.aggregation_type, flat),
#                'funding_organizations': self.get_funding_organisations(measure),
#                'status_moments': measure.get_statusmoments(auto_create_missing_states=True, only_valid=True),
#            })
#
#        if size >= self.COMPLETE:
#            output.update({
#                'read_only': measure.read_only,
#                'import_raw': measure.import_raw,
#                'import_source': measure.import_source,
#            })
#
#        if include_geom:
#            output.update({
#                'geom': measure.get_geometry_wkt_string(),
#            })
#
#        return output
#
#    def update_many2many(self, record, model_field, linked_records):
#        """
#            update specific part of manyToMany relations.
#            input:
#                - record: measure
#                - model_field. many2many field object
#                - linked_records. list with dictionaries with:
#                    id: id of related objects
#                    optional some relations in case the relation is through another object
#
#        """
#
#        if model_field.name == 'funding_organizations':
#            record.set_fundingorganizations(linked_records)
#        if model_field.name == 'status_moments':
#            record.set_statusmoments(linked_records)
#        else:
#            #areas, waterbodies, category
#            self._save_single_many2many_relation(record, model_field, linked_records)

    ####### base get object #######

    def get(self, request):
        """
            returns object or list of objects

        """

        object_id = self._str2int_or_none(request.GET.get('object_id', None))
        size = request.GET.get('size', 'complete')
        flat = self._str2bool_or_none(request.GET.get('flat', False))
        include_geom =  self._str2bool_or_none(request.GET.get('include_geom', True))
        show_deleted = self._str2bool_or_none(request.GET.get('show_deleted', False))


        size = self.size_dict[size.lower()]

        model = self.model_class

        logger.debug("""input for api is:
                object_id: %s
                size: %s
                include_geom; %s
                flat: %s
              """%(str(object_id), str(size), str(include_geom), str(flat)))

        if object_id is not None:
            #return single object
            obj  = model.objects.get(id=object_id)
            output = self.get_object_for_api(obj, flat=flat, size=size, include_geom=include_geom)
            return {'success': True, 'data': output}

        else:
            #return list with objects
            start = int(request.GET.get('start', 0))
            limit = int(request.GET.get('limit', 25))
            query = request.GET.get('query', None)

            output = []

            objs = model.objects.all()

            if not show_deleted and self.valid_field:
                objs = objs.filter(**{self.valid_field: self.valid_value})


            if query:
                for q in query.split(','):
                    q = q.split(':')
                    objs = objs.filter(**{q[0]:q[1]})

            for obj in objs[start:(start+limit)]:
                output.append(self.get_object_for_api(obj, flat=flat, size=size, include_geom=include_geom))

            return {'success': True, 'data': output, 'count': objs.count()}


    #########functions around a post (update, create, delete) ########

    def post(self, request):
        """
            Update, create or delete records

        """

        #request params
        action = request.GET.get('action', None)
        size =  request.GET.get('size', 'complete')
        flat =  self._str2bool_or_none(request.GET.get('flat', False))
        include_geom =  self._str2bool_or_none(request.GET.get('include_geom', True))
        data = json.loads(self.CONTENT.get('data', []))
        edit_message = self.CONTENT.get('edit_message', None)

        size = self.size_dict[size.lower()]


        logger.debug("""input for api is:
                action: %s
                data: %s
                edit_message: %s
              """%(str(action), str(data), str(edit_message)))


        output = None
        touched_objects = None

        if type(data) == dict:
            #get single object and return single object
            return_dict = True
            data = [data]
        else:
            return_dict = False

        if action == 'delete':#OK
            success = self.delete_objects(
                data)
        elif action == 'create':#todo
            success, touched_objects = self.create_objects(
                data)
        elif action == 'update':
            success, touched_objects = self.update_objects(
                data)
        else:
            logger.error("Unkown post action '%s'." % action)
            success = False

        if touched_objects:
            output = []
            for obj in touched_objects:
                output.append(self.get_object_for_api(obj, flat=flat, size=size, include_geom=include_geom))

            if return_dict:
                #just return single object
                output = output[0]

        return {'success': success,
                'data': output}



    def create_objects(self, data):
        Exception('not implemented yet')


    def update_objects(self, data):
        """
            Update records

            issues(todo):
            - everything in one database transaction
        """
        touched_objects = []
        model = self.model_class

        success = True

        for item in data:
            record = model.objects.get(pk=item['id'])
            touched_objects.append(record)

            for (key, value) in item.items():
                key = str(key)

                try:
                    model_field = model._meta.get_field(key)

                    if model_field.rel is not None and type(model_field.rel) == models.ManyToManyRel:
                        self.update_many2many(record, model_field, value)
                    else:
                        if type(model_field.rel) == models.ManyToOneRel:
                            #input is a dictionary with an id and name in json
                            if value is None or value == {} or value == []:
                                value = None
                            else:
                                if type(value) == list:
                                    value = value[0]
                                value = model_field.rel.to.objects.get(pk=value['id'])

                        if type(model_field) == models.IntegerField and len(model_field._get_choices()) > 0:
                            #input is a dictionary with an id and name in json
                            if value is None or value == {} or value == []:
                                value = None
                            else:
                                if type(value) == list:
                                    value = value[0]
                                value = value['id']

                        if isinstance(model_field, models.IntegerField):
                            value = self._str2int_or_none(value)
                        setattr(record, key, value)

                        if isinstance(model_field, models.FloatField):
                            value = self._str2float_or_none(value)
                        setattr(record, key, value)

                        if isinstance(model_field, models.BooleanField):
                            value = self._str2bool_or_none(value)
                        setattr(record, key, value)

                        if isinstance(model_field, models.GeometryField):
                            if value is None or value == '':
                                value = None
                            else:
                                reader = WKTReader()
                                value = reader.read(value)

                        setattr(record, key, value)

                except FieldDoesNotExist:
                    logger.error("Field %s.%s not exists." % (
                            model._meta.module_name, key))
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
                object = model.objects.filter(
                    pk=object_id)
                if not object.exists():
                    continue
                object = object[0]
                setattr(object, self.valid_field, not self.valid_value)
                object.save()
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
                    optional some relations in case the relation is through another object

        """
        model_link = getattr(record, model_field.name)
        existing_links = dict([(obj.id, obj) for obj in model_link.all()])

        for linked_record in linked_records:

            if existing_links.has_key(linked_record['id']):
                #update record
                link = existing_links[linked_record['id']]
                link.save()
                del existing_links[linked_record['id']]
            else:
                #create new
                model_link.add(
                    model_field.rel.to.objects.get(pk=linked_record['id']))

        #remove existing links, that are not anymore
        for link in existing_links.itervalues():
            model_link.remove(link)


    def save_single_many2many_relation(self, record, model_field, linked_records):
        """
            update specific part of manyToMany relations.
            input:
                - record: measure
                - model_field. many2many field object
                - linked_records. list with dictionaries with:
                    id: id of related objects
                    optional some relations in case the relation is through another object

        """

        model_link = getattr(record, model_field.name)
        existing_links = dict([(obj.id, obj) for obj in model_link.all()])

        for linked_record in linked_records:

            if existing_links.has_key(linked_record['id']):
                #update record
                link = existing_links[linked_record['id']]
                link.save()
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
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.error('value %s is not a float'%str(value))
            return None


    def _str2int_or_none(self, value):
        """
            returns integer of value, or when not a number returns 'None'
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.error('value %s is not an integer'%str(value))
            return None

    def _str2bool_or_none(self, value):
        """
            returns integer of value, or when not a number returns 'None'
        """
        if type(value) == bool:
            return value
        elif type(value) in (str, unicode):
            if value.lower in ('true', '1', 'on'):
                return True
            elif value.lower in ('false', '0', 'off'):
                return False
            else:
                return None
        elif type(value) in (int, float):
            return bool(value)
        else:
            return None