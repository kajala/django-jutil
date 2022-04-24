import logging
from email.utils import parseaddr  # pylint: disable=import-error
from typing import Optional, Union, Tuple, Sequence, List
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from base64 import b64encode
from os.path import basename

logger = logging.getLogger(__name__)


def make_email_recipient(val: Union[str, Tuple[str, str]]) -> Tuple[str, str]:
    """
    Returns (name, email) tuple.
    :param val:
    :return: (name, email)
    """
    if isinstance(val, str):
        res = parseaddr(val.strip())
        if len(res) != 2 or not res[1]:
            raise ValidationError(_("Invalid email recipient: {}".format(val)))
        return res[0] or res[1], res[1]
    if len(val) != 2:
        raise ValidationError(_("Invalid email recipient: {}".format(val)))
    return val


def make_email_recipient_list(recipients: Optional[Union[str, Sequence[Union[str, Tuple[str, str]]]]]) -> List[Tuple[str, str]]:
    """
    Returns list of (name, email) tuples.
    :param recipients:
    :return: list of (name, email)
    """
    out: List[Tuple[str, str]] = []
    if recipients is not None:
        if isinstance(recipients, str):
            recipients = recipients.split(",")
        for val in recipients:
            if not val:
                continue
            out.append(make_email_recipient(val))
    return out


def send_email(  # noqa
    recipients: Sequence[Union[str, Tuple[str, str]]],
    subject: str,
    text: str = "",
    html: str = "",
    sender: Union[str, Tuple[str, str]] = "",
    files: Optional[Sequence[str]] = None,
    cc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
    bcc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
    exceptions: bool = False,
) -> int:
    """
    Sends email. Supports both SendGrid API client and SMTP connection.
    See send_email_sendgrid() for SendGrid specific requirements.

    :param recipients: List of "To" recipients. Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param subject: Subject of the email
    :param text: Body (text), optional
    :param html: Body (html), optional
    :param sender: Sender email, or settings.DEFAULT_FROM_EMAIL if missing
    :param files: Paths to files to attach
    :param cc_recipients: List of "Cc" recipients (if any). Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param bcc_recipients: List of "Bcc" recipients (if any). Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param exceptions: Raise exception if email sending fails. List of recipients; or single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :return: Status code 202 if emails were sent successfully
    """
    if hasattr(settings, "EMAIL_SENDGRID_API_KEY") and settings.EMAIL_SENDGRID_API_KEY:
        return send_email_sendgrid(recipients, subject, text, html, sender, files, cc_recipients, bcc_recipients, exceptions)
    return send_email_smtp(recipients, subject, text, html, sender, files, cc_recipients, bcc_recipients, exceptions)


def send_email_sendgrid(  # noqa
    recipients: Sequence[Union[str, Tuple[str, str]]],
    subject: str,
    text: str = "",
    html: str = "",
    sender: Union[str, Tuple[str, str]] = "",
    files: Optional[Sequence[str]] = None,
    cc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
    bcc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
    exceptions: bool = False,
    api_key: str = "",
) -> int:
    """
    Sends email using SendGrid API. Following requirements:
    * pip install sendgrid>=6.3.1,<7.0.0
    * settings.EMAIL_SENDGRID_API_KEY must be set and

    :param recipients: List of "To" recipients. Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param subject: Subject of the email
    :param text: Body (text), optional
    :param html: Body (html), optional
    :param sender: Sender email, or settings.DEFAULT_FROM_EMAIL if missing
    :param files: Paths to files to attach
    :param cc_recipients: List of "Cc" recipients (if any). Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param bcc_recipients: List of "Bcc" recipients (if any). Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param exceptions: Raise exception if email sending fails. List of recipients; or single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param api_key: Optional Sendgrid API key. Default settings.EMAIL_SENDGRID_API_KEY.
    :return: Status code 202 if emails were sent successfully
    """
    try:
        import sendgrid  # type: ignore  # pylint: disable=import-outside-toplevel
        from sendgrid.helpers.mail import Content, Mail, Attachment  # type: ignore  # pylint: disable=import-outside-toplevel
        from sendgrid import ClickTracking, FileType, FileName, TrackingSettings  # type: ignore  # pylint: disable=import-outside-toplevel
        from sendgrid import Personalization, FileContent, ContentId, Disposition  # type: ignore  # pylint: disable=import-outside-toplevel
    except Exception as err:
        raise Exception("Using send_email_sendgrid() requires sendgrid pip install sendgrid>=6.3.1,<7.0.0") from err

    if not api_key and hasattr(settings, "EMAIL_SENDGRID_API_KEY"):
        api_key = settings.EMAIL_SENDGRID_API_KEY
    if not api_key:
        raise Exception("EMAIL_SENDGRID_API_KEY not defined in Django settings and API key not passed in to send_email_sendgrid() either")

    if files is None:
        files = []
    from_clean = make_email_recipient(sender or settings.DEFAULT_FROM_EMAIL)
    recipients_clean = make_email_recipient_list(recipients)
    cc_recipients_clean = make_email_recipient_list(cc_recipients)
    bcc_recipients_clean = make_email_recipient_list(bcc_recipients)
    subject = strip_tags(subject)

    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        text_content = Content("text/plain", text) if text else None
        html_content = Content("text/html", html) if html else None

        personalization = Personalization()
        for recipient in recipients_clean:
            personalization.add_email(sendgrid.To(email=recipient[1], name=recipient[0]))
        for recipient in cc_recipients_clean:
            personalization.add_email(sendgrid.Cc(email=recipient[1], name=recipient[0]))
        for recipient in bcc_recipients_clean:
            personalization.add_email(sendgrid.Bcc(email=recipient[1], name=recipient[0]))

        mail = Mail(
            from_email=sendgrid.From(email=from_clean[1], name=from_clean[0]),
            subject=subject,
            plain_text_content=text_content,
            html_content=html_content,
        )
        mail.add_personalization(personalization)

        # stop SendGrid from replacing all links in the email
        mail.tracking_settings = TrackingSettings(click_tracking=ClickTracking(enable=False))

        for filename in files:
            if filename:
                with open(filename, "rb") as fp:
                    attachment = Attachment()
                    attachment.file_type = FileType("application/octet-stream")
                    attachment.file_name = FileName(basename(filename))
                    attachment.file_content = FileContent(b64encode(fp.read()).decode())
                    attachment.content_id = ContentId(basename(filename))
                    attachment.disposition = Disposition("attachment")
                    mail.add_attachment(attachment)

        mail_body = mail.get()
        res = sg.client.mail.send.post(request_body=mail_body)

        if res.status_code == 202:
            logger.info("EMAIL_SENT %s", {"to": recipients, "subject": subject, "status": res.status_code})
        else:
            logger.info(
                "EMAIL_ERROR %s",
                {"to": recipients, "subject": subject, "status": res.status_code, "body": res.body},
            )

    except Exception as err:
        logger.error("EMAIL_ERROR %s", {"to": recipients, "subject": subject, "exception": str(err)})
        if exceptions:
            raise
        return -1

    return res.status_code


def send_email_smtp(  # noqa
    recipients: Sequence[Union[str, Tuple[str, str]]],
    subject: str,
    text: str = "",
    html: str = "",
    sender: Union[str, Tuple[str, str]] = "",
    files: Optional[Sequence[str]] = None,
    cc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
    bcc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
    exceptions: bool = False,
) -> int:
    """
    Sends email using SMTP connection using standard Django email settings.

    For example, to send email via Gmail:
    (Note that you might need to generate app-specific password at https://myaccount.google.com/apppasswords)

        EMAIL_HOST = 'smtp.gmail.com'
        EMAIL_PORT = 587
        EMAIL_HOST_USER = 'xxxx@gmail.com'
        EMAIL_HOST_PASSWORD = 'xxxx'  # noqa
        EMAIL_USE_TLS = True

    :param recipients: List of "To" recipients. Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param subject: Subject of the email
    :param text: Body (text), optional
    :param html: Body (html), optional
    :param sender: Sender email, or settings.DEFAULT_FROM_EMAIL if missing
    :param files: Paths to files to attach
    :param cc_recipients: List of "Cc" recipients (if any). Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param bcc_recipients: List of "Bcc" recipients (if any). Single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :param exceptions: Raise exception if email sending fails. List of recipients; or single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)  # noqa
    :return: Status code 202 if emails were sent successfully
    """
    if files is None:
        files = []
    from_clean = make_email_recipient(sender or settings.DEFAULT_FROM_EMAIL)
    recipients_clean = make_email_recipient_list(recipients)
    cc_recipients_clean = make_email_recipient_list(cc_recipients)
    bcc_recipients_clean = make_email_recipient_list(bcc_recipients)
    subject = strip_tags(subject)

    try:
        mail = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email='"{}" <{}>'.format(*from_clean),
            to=['"{}" <{}>'.format(*r) for r in recipients_clean],
            bcc=['"{}" <{}>'.format(*r) for r in bcc_recipients_clean],
            cc=['"{}" <{}>'.format(*r) for r in cc_recipients_clean],
        )
        for filename in files:
            if filename:
                mail.attach_file(filename)
        if html:
            mail.attach_alternative(content=html, mimetype="text/html")

        mail.send(fail_silently=False)
        logger.info("EMAIL_SENT %s", {"to": recipients, "subject": subject})

    except Exception as e:
        logger.error("EMAIL_ERROR %s", {"to": recipients, "subject": subject, "exception": str(e)})
        if exceptions:
            raise
        return -1

    return 202
