django-jutil
============

Collection of small utilities for Django and Django REST framework projects.

Features
========

* Simplified admin changes history logging (admin_log)
* ModelAdmin with read/write permissions separated (ModelAdminBase)
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
* Event logging with systematic format for easy parsing/grepping (log_event)
* Django middleware for exception logging/emailing (LogExceptionMiddleware)
* Django middleware for language cookie handling (EnsureLanguageCookieMiddleware)
* Utilities or Django Model handling (e.g. clone_model, get_object_or_none)
* Utilities for parsing booleans and datetime values (using pytz)
* Simple user field based permission checking for REST APIs (permissions.py)
* Geo IP / IP info functions (request.py)
* CSV download response (CsvFileResponse)
* Simple SMS sending (send_sms)
* Mixin for basic test user setup (DefaultTestSetupMixin)
* Unit tests for bunch of stuff (tests.py)
* URL modifying/comparison functions (urls.py)
* Validators and filters for various types (validators.py)
* XML Element to/from dict conversions (dict_to_element, xml_to_dict)

Install
=======

pip install django-jutil

