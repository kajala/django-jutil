django-jutil
============

Collection of small utilities for Django and Django REST framework projects.

Features
========

* Simplified admin changes history logging (admin_log)
* ModelAdmin with length limited history view (ModelAdminBase)
* Simplified object URL/link generation within admin (admin_obj_link and admin_obj_url)
* Extended admin log mixin of changed fields (AdminLogEntryMixin)
* Admin file download mixin with file permission checks (AdminFileDownloadMixin)
* User authentication helpers (require_auth, AuthUserMixin)
* Mixin for cached model fields management (CachedFieldsMixin)
* BaseCommand extension which catches, logs and emails errors (SafeCommand)
* Command options for simplified handling of date ranges (add_date_range_arguments, parse_date_range_arguments)
* Various utilities for date ranges generation and iteration (dates.py)
* Utilities for dict sorting and formatting, choices list label fetching (dict.py)
* Simplified email sending via SendGrid API (send_email)
* Various formatting utilities (e.g. XML, timedelta, Decimal)
* Decimal encoder for encoding JSON objects/dictionaries containing Decimal instances (SimpleDecimalEncoder)
* Django middleware for exception logging/emailing (LogExceptionMiddleware)
* Django middleware for language cookie handling (EnsureLanguageCookieMiddleware)
* Django middleware for user.profile.timezone based timezone activation
* Utilities or Django Model handling (e.g. clone_model, get_object_or_none)
* Utilities for parsing booleans and datetime values (using pytz)
* Simple user field based permission checking for REST APIs (permissions.py)
* Geo IP / IP info functions using IPStack API (request.py)
* Download responses (FileSystemFileResponse and CsvFileResponse)
* Simple SMS sending (send_sms)
* Mixin for basic test user setup (DefaultTestSetupMixin)
* Pretty good unit test coverage (tests.py)
* URL modifying/comparison functions (urls.py)
* Validators and filters for various types (validators.py)
* XML Element to/from dict conversions (dict_to_element, xml_to_dict)
* XML file/content pretty formatting (format_xml, format_xml_bytes, format_xml_file, FormattedXmlResponse)

Install
=======

pip install django-jutil


Test Code Coverage
==================

* `coverage run manage.py; coverage report`


Changes
=======

3.0.0:
+ Django 3.0.4 compatibility

2.4.14:
+ Unit test improvements etc.

2.3.2:
+ Prospector clean & checked when making new release

2.3.1:
+ Cleanup related to prospector results (https://pypi.org/project/prospector/)

2.2.42:
+ ElementTree usage cleanup

2.2.38:
+ Added FormattedXmlResponse

2.2.37:
+ Added format_xml_bytes

2.2.35:
+ Some clearing code fixes for Sweden

2.2.31:
+ Added various sanitizer-functions where simple validation is too strict

2.2.25:
+ Added fi_ssn_generator (fake/test Finnish social security numbers)

2.2.22:
+ Some localization improvements

2.2.17:
+ Added format_xml_file, format_xml

2.2.14:
+ More unit tests

2.2.12:
+ Added admin_obj_link and admin_obj_url

2.2.11:
+ Sweden bank info fixes

2.2.8:
+ Denmark bank info

2.2.7:
+ More unit tests

2.2.6:
+ IBAN validation of more or less all IBAN countries

2.2.5:
+ Belgium IBAN validator

2.2.3:
+ ElementTree import cleanup (thanks to https://github.com/kutera)

2.2.0:
+ Belgium IBAN validation support (thanks to https://github.com/kutera)
