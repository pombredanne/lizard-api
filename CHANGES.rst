Changelog of lizard-api
===================================================


0.16 (unreleased)
-----------------

- Nothing changed yet.


0.15 (2013-01-24)
-----------------

- Fix error on save a measure pp411.


0.14 (2012-12-11)
-----------------

- Fix error on update measure.


0.13 (2012-11-29)
-----------------

- Split post function of BaseApiView class pp397.

- Fix pep8 errors.


0.12 (2012-10-11)
-----------------

- Remove duplicate definition, and some print statements.

- Remove save() statement on update linked records.


0.11.1 (2012-04-15)
-------------------

- bug fix for saving one2many fields. added function update_one2many for this kind of
      relations (part of pp issue 187)


0.11 (2012-04-11)
-----------------

- Add extra exception for parsing post data.


0.10 (2012-03-12)
-----------------

- bug fix for setting related relations to zero

- added slug option for selecting item (beside id)


0.9 (2012-03-05)
----------------

- bug fix for many2many relations

0.8 (2012-02-27)
----------------

- added filter option

- string, bool or number field also dict allowed with value as id


0.7 (2012-02-17)
----------------

- In create_objects, BaseApiView:
    - Fix for read_only_fields
    - Put edit_summary on obj instance


0.6 (2012-02-13)
----------------

- Add the summary as attribute on record when updating objects.
- Add read-only options to fields (fields are ignored during update and create)
- fix for read_only_fields


0.5 (2012-02-08)
----------------

- added create function


0.4 (2012-01-31)
----------------

- added sort functionality


0.3 (2012-01-13)
----------------

- improved base class


0.2 (2012-01-13)
----------------

- Added base class for Api's


0.1 (2011-10-18)
----------------

- Initial library skeleton created by nensskel.  [your name]
