django-jutil
============

Collection of small utilities for Django and Django REST framework projects.

Features
========

* Simplified admin changes history logging (admin_log)
* ModelAdmin with length limited history view (ModelAdminBase)
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

Install
=======

pip install django-jutil


Changes
=======

2.2.3:
+ ElementTree import cleanup (thanks to https://github.com/kutera)

2.2.0:
+ Belgium IBAN validation support (thanks to https://github.com/kutera)
