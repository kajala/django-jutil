django-jutil
============

Collection of small utilities for Django and Django REST framework projects.
Django 3.0 compatible. 

[![codecov](https://codecov.io/gh/kajala/django-jutil/branch/master/graph/badge.svg)](https://codecov.io/gh/kajala/django-jutil)
[![Build Status](https://travis-ci.org/kajala/django-jutil.svg?branch=master)](https://travis-ci.org/kajala/django-jutil)


Features
========

* Simplified admin changes history logging (admin_log)
* ModelAdmin with length limited history view (ModelAdminBase)
* Simplified object URL/link generation within admin (admin_obj_link and admin_obj_url)
* Extended admin log with changed field values and user IP (ModelAdminBase)
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


Notes About Features
====================

Extended Admin Logging
----------------------
jutil.ModelAdminBase supports (by default) extended logging using Django's native LogEntry' change_message 
JSON field. Normally Django logs only field verbose names but jutil implementation
logs changed field names and values and user IP as well to the same change_message JSON field.
To actually show output from this extended logging data you need to format change_message using 
format_change_message_ex filter. The default ModelAdminBase object history template (jutil/admin/object_history.html) uses it. 



Static Code Analysis
====================

The library passes both prospector and mypy checking. To install:

pip install prospector
pip install mypy

To analyze:

prospector
mypy .


Test Code Coverage
==================

* `coverage run manage.py; coverage report`


Notes About Email Configurations
================================

# Microsoft 365 (2022)
EMAIL_HOST = "smtp.office365.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = (microsoft 365 email account)
SERVER_EMAIL = EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = (email password)
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 60

# SendGrid (2022)
EMAIL_SENDGRID_API_KEY = (api_key)
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = (sendgrid api key)


Changes
=======

3.11.1:
* REMOVED: AdminLogEntryMixin, no longer needed as ModelAdminBase logs everything automatically
* REMOVED: admin_log_changed_fields, no longer needed as ModelAdminBase logs everything automatically
* RENAMED: get_model_keys -> get_model_field_names, for consistent naming with Django

3.7.4:
* Stricter get_media_full_path and is_media_full_path

3.7.3:
* Unit tests
* Get media full path cleanup

3.7.2:
* Cleanup

3.7.1:
* Requirements.txt: deleted optional dependency sendgrid, add sendgrid on project level sendgrid>=6.3.1,<7.0.0
* Deleted deprecated auth.require_auth, use auth.get_auth_user and auth.get_auth_user_or_none
* Deleted deprecated dict.choices_label and dict.dict_to_html, use format.choices_label and format.format_dict_as_html
* Deleted deprecated logs.*, use logging directly
* Deleted deprecated object.*, use type-safer alternatives
* Deleted deprecated url_equals and url_host, use urlparse directly
* Removed deprecated testing.*
* Cleaned up parse_datetime, parse_bool, parse_datetime_or_none and parse_bool_or_none
* Simpler cleaned up testing mixin TestSetupMixin   

3.6.11:
* Deprecated object.get/set obj attr functions
* Deprecated url equals and url host
* Deprecated testing.DefaultTestSetupMixin
* Separated parse functions /w xxx or none versions for better typing support
* Dropped python-dateutil dependency, added unit tests for get time steps
* Deprecated log event
* Updated send_email_sendgrid docs
* Refactored choices label and dict to html in dict and format, added deprecation warnings
* Added --this-month, --this-week, --this-year to add date range arguments, get date range by name, parse date range arguments
* Require auth refactoring
* Removed AdminFileDownloadMixin - Django 3.1 has new logic for uploaded file URL format making the mixin obsolete
* (origin/master, origin/HEAD, master) README update

3.6.10:
* Unit test fix
* Log entry ordering fix

3.6.9:
* Minor refactoring

3.6.8:
* API testing client to support non-json content
* Parse bool unit test

3.6.7:
* Added format as html json and unit tests

3.6.6:
* Millisecond handling to format timedelta
* Deploy cleanup
* Python-dotenv

3.6.5:
* API testing tweaks

3.6.4:
* Mypy fix
* Unit test improvements, added support for FI ssns before 1900 and after 2000
* Test-coverage tweak

3.6.3:
* Code QA / Prospector fixes
* Added wait object or none and unit test

3.6.2:
* Added .env to ignore

3.6.1:
* Cleanup
* Dropped parse sftp connection (as redundant)
* Docs

3.5.3:
* Tweaks to usage of ipware

3.5.2:
* Minor refactoring

3.5.1:
* Upgrade of ipware to newer version
* Dev requirements change of psycopg2

3.4.9:
* Mypy fix
* Added get_ip() wrapper for ipware

3.4.8:
* Usage cleanup of ipware

3.4.7:
* Minor refactoring, added unit tests

3.4.6:
* More relaxed typing to admin log
* DB check to build process

3.4.5:
* Format table max col setting fix
* Fixed format table bug, added docs

3.4.4:
* Added User as explicit opt parameter to admin log

3.4.3:
* Minor refactoring

3.4.2:
* Added strip tag fields and unit tests

3.4.1:
* Type checking fixes
* Added middleware unit tests
* Changed ActivateUserProfileTimezone -> ActivateUserProfileTimezoneMiddleware to conform Django naming conventions
* Cleanup, docs
* Test-coverage script tweaks
* Added dependency-check to requirements-dev.txt
* .gitignore tweaks

3.3.6:
* Unit test fix
* Build process cleanup
* Cleanup
* Test-coverage script update
* Added htmlcov to ignore

3.3.5:
* Test fixes
* Admin obj url fix

3.3.4:
* Admin log type fix

3.3.3:
* Code QA
* Unit test improvements
* Updated travis test to python 3.8

3.3.2:
* Added camel case conversion funcs

3.3.1:
* Format timedelta cleanup
* Test-coverage script update
* Unit test fixes
* Re-enabled pytype

3.2.21:
* Email fix

3.2.20:
* Unit test coverage update
* Sendgrid email format fix

3.2.19:
* Added end_of_month() (as in Excel) and unit tests
* L10n

3.2.18:
* Type checking fixes

3.2.17:
* Type checking fixes

3.2.16:
* Type checking fixes

3.2.15:
* CachedFieldsMixin save() TYPE CHECKING fix

3.2.14:
* Type checking fix
* Readme updates
* MANIFEST tweaks
* Pre-release script tweaks

3.2.13:
* Added py.typed marker file

3.2.12:
* Mypy / cleanup

3.2.11:
* Test coverage update
* Added twine to dev reqs
* Deploy script update

3.2.10:
* Test coverage update
* Mypy support

3.2.9:
* Test coverage update
* Pre-release script tweaks
* Test coverage script tweaks

3.2.8:
* Travis sys import
* Added vanity icons to readme

3.2.7:
* Added sudo apt-get install -y libxml2-utils to travis

3.2.6:
* Travis log changes

3.2.5:
* Added travis config

3.2.4:
* Codecov tests

3.2.3:
* Added codecov.yml

3.2.2:
* Test coverage update

3.2.1:
* Dependency cleanup

3.1.4:
* Test coverage update
* Language cookie to use secure and httponly settings
* Updated LICENSE.txt

3.1.3:
* Test coverage update
* Cleanup
* IBAN generation

3.1.2:
* Test coverage update
* Config tweaks / pytype

3.1.1:
* Test coverage update

3.0.16:
* Test coverage update
* Code QA pytype tool integration to build process

3.0.15:
* Formatting options to format timedelta as 3h40min14s

3.0.14:
* Test coverage update
* Added helpers for media path handling

3.0.13:
* BIC validator
* Added body and subject to test email

3.0.12:
* Test coverage update
* CsvFileResponse -> CsvResponse to be consistent with naming of other responses
* Separate XmlResponse and XmlFileResponse

3.0.11:
* Test coverage update
* Cleanup

3.0.10:
* Test coverage update
* Cleanup
* Xml formatting error reporting

3.0.9:
* Test coverage update
* Xml content decoding fix on error
* L10n
* Email unit tests

3.0.8:
* Test coverage update
* Test email sending tweaks
* More unit tests

3.0.7:
* Test coverage update
* Pre-release step update

3.0.6:
* Deploy tweaks
* Added coverage report
* Cleanup, deleted format xml (unnecessary since multiple tools for that)

3.0.5:
* Changed SafeCommand to be compatible with BaseCommand on Exception return

3.0.4:
* Unit tests, refactoring

3.0.3:
* Added ucfirst and ucfirst lazy

3.0.2:
* Added format table
* Added test-coverage script
* Docs

3.0.1:
* Prospector 1.2.0 fixes
* Django 3.0 compatibility

2.4.14:
* Unit tests, model changed check

2.4.13:
* Assert tweaks
* File download admin tweaks
* Admin download link fix

2.4.12:
* Support for multiple file fields in AdminFileDownloadMixin

2.4.11:
* Prospector / code QA fixes
* Added SMTP based email support, logging

2.4.10:
* Deploy fix

2.4.9:
* Deploy cleanup and tweaks

2.4.8:
* Improved testing coverage
* Coverage tweaks
* Added .coverage to .gitignore
* Removed coverage

2.4.7:
* Noqa fixes (prospector)
* Added .coveragerc
* Doc tweaks
* Sftp connection string parsing cleanup

2.4.6:
* Sftp connection string parsing

2.4.5:
* Sendgrid api usage fix

2.4.4:
* Added base url support to admin links

2.4.3:
* Disabled sendgrid click tracking by default

2.4.2:
* Updated to use sendgrid v3 api, added cc and bcc support

2.4.1:
* Reg id -> org id name refactoring

2.3.5:
* Format keys option to dict to html

2.3.4:
* Added fi company reg id generator

2.3.3:
* Admin helper stweaks
* Admin file download tweak
* Pre-release process
* Docs

2.3.2:
* Deploy tweaks
* Prospector check to build
* Prospector clean

2.3.1:
* Code cleanup

2.2.43:
* Etree related refactoring

2.2.42:
* ElementTree usage fix

2.2.41:
* Updated requirements
* Cleaned up ugettext usage 

2.2.40:
* ElementTree cleanup, issues related to isinstance() usage

2.2.39:
* Separate FormattedXmlResponse and FormattedXmlFileResponse

2.2.38:
* Added FormattedXmlResponse

2.2.37:
* Format xml bytes

2.2.36:
* Format xml file improvements
* Advanced xml formatting using xmllint

2.2.35:
* Sweden clearing code fixes

2.2.34:
* Localized actions list sorting

2.2.33:
* Dict to html unit test
* Dict to html fix

2.2.32:
* Improved dict formatting

2.2.31:
* Added some sanitizers to validators.py

2.2.30:
* Admin obj link None handling

2.2.29:
* Nordea Sweden clearing code additions

2.2.28:
* Minor refactoring

2.2.27:
* Added obj tools

2.2.26:
* Debug code cleanup

2.2.25:
* Fi ssn generator fix

2.2.24:
* Added fi ssn generator

2.2.23:
* Nordea/SE clearing number addition
* Deploy cleanup

2.2.22:
* Added changelist view download support to AdminFileDownloadMixin

2.2.21:
* Unit tests
* L10n check
* Cleanup

2.2.20:
* Generic country filtering
* Docs

2.2.19:
* Added one NordeaAB clearing code range

2.2.18:
* Fixed non-xmllint xml data formatting
* Added format xml command

2.2.17:
* Added format xml file helper

2.2.16:
* Media path stripping

2.2.15:
* Int conversion fix / validators
* Unit test tweaks
* Better unit tests

2.2.13:
* Added missing Nordea AB / Sweden clearing number
* Clarification / swedish clearing code

2.2.12:
* Added admin obj link and admin obj url

2.2.11:
* Sweden clearing code filtering

2.2.10:
* Reduced Swedbank account number length requirement

2.2.9:
* Unit tests

2.2.8:
* Dk bank info

2.2.7:
* Unit test
* Sparbanken Syd account number length

2.2.6:
* Belgium iban data to 4 spaces instead of 8
* Validation of all iban countries

2.2.5:
* Added be iban validator, refactoring validator code a bit
* Doc cleanup

2.2.4:
* Docs

2.2.3:
* Element tree cleanup

2.2.2:
* Unified xml.etree.ElementTree.Element usage

2.2.1:
* Adding BE (Belgium) bic bank to iban bic validators (thanks kutera/master)

2.1.24:
* Sweden bank const fix

2.1.23:
* Unit test fixes
* Swedish bank const cleanup

2.1.22:
* Swedish bank clearing code fixes

2.1.21:
* Validator return space fix

2.1.20:
* Added ascii filter and unit tests

2.1.19:
* Refactoring
* Swedish bank const php generation

2.1.18:
* Cleanup

2.1.17:
* Updated bank constants, added Sweden

2.1.16:
* Added ActivateUserProfileTimezone middleware

2.1.15:
* Upgraded external dependencies, added days to time delta

2.1.14:
* Upgraded external dependencies

2.1.13:
* Age calculation

2.1.12:
* Upgraded django

2.1.11:
* Iso payment ref validator

2.1.10:
* Email filtering tweaks

2.1.9:
* Email filter tweak

2.1.8:
* Dependency upgrade

2.1.7:
* Error message improvements

2.1.6:
* Selective cached fields update

2.1.5:
* Added simple email validator

2.1.4:
* Company reg id validator tweak

2.1.3:
* Dropped separate read/write views since Django supports this natively

2.1.2:
* Dependency upgrade

2.1.1:
* Upgraded version to match django version

1.2.11:
* Bank info unit test fix, upgraded libs

1.2.10:
* Admin log convention change: user system username instead of the first user in the system

1.2.9:
* Iban bank info convention change
* Tests
* Version bump
* Iban bank info to return None, None to be more consistent with normal output

1.2.7:
* Replaced freegeoip.net API with ipstack.com

1.2.6:
* Unit tests and cleanup

1.2.5:
* Prev 30d, 60d and 90d time ranges

1.2.4:
* 404 check

1.2.3:
* Docs and cleanup

1.2.2:
* Minor version bump
* Admin file download cleanup

1.1.12:
* File download response cleanup

1.1.11:
* SafeCommand return value

1.1.10:
* Parse requirements compatibility

1.1.9:
* Gz .gitignore
* Cleanup
* Parse requirements fix

1.1.8:
* Cleanup
* Replaced parse requirements (fix)

1.1.7:
* Replaced parse requirements

1.1.6:
* FI company reg id check filtering

1.1.5:
* Extended FI company reg id acceptance

1.1.4:
* Permissions fix

1.1.3:
* Renamed passwd -> setpass to avoid name collision with django extensions project

1.1.2:
* Tests

1.1.1:
* Cleanup

1.0.5:
* Removed obsolete SimpleJsonDecoder since Django has better one now
* Language cookie fix

1.0.4:
* Unit test fix

1.0.3:
* Fi bank const update

1.0.2:
* Unit tests
* Dependency fix
* Twine up

1.0.1:
* Cleanup
* Docs

1.0.0:
* Docs
* Github repository init
