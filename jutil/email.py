import logging
from typing import Optional, Union, Tuple, Sequence, List
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import now
from jutil.logs import log_event
from base64 import b64encode
from os.path import basename


logger = logging.getLogger(__name__)


def make_email_recipient(val: Union[str, Tuple[str, str]]) -> str:
    if isinstance(val, str):
        return val
    if len(val) != 2:
        raise ValidationError('Email recipient invalid format: {}'.format(val))
    return '"{}" <{}>'.format(*val)


def make_email_recipient_list(recipients: Optional[Union[str, Sequence[Union[str, Tuple[str, str]]]]]) -> List[str]:
    if recipients is None:
        return []
    if isinstance(recipients, str):
        return [str(r).strip() for r in recipients.split(',')]
    out: List[str] = []
    for val in recipients:
        if not val:
            continue
        out.append(make_email_recipient(val))
    return out


def send_email(recipients: Sequence[Union[str, Tuple[str, str]]], subject: str,  # noqa
               text: str = '', html: str = '',
               sender: str = '',
               files: Optional[Sequence[str]] = None,
               cc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
               bcc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
               exceptions: bool = False):
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
    if hasattr(settings, 'EMAIL_SENDGRID_API_KEY') and settings.EMAIL_SENDGRID_API_KEY:
        return send_email_sendgrid(recipients, subject, text, html, sender, files, cc_recipients, bcc_recipients, exceptions)
    return send_email_smtp(recipients, subject, text, html, sender, files, cc_recipients, bcc_recipients, exceptions)


def send_email_sendgrid(recipients: Sequence[Union[str, Tuple[str, str]]], subject: str,  # noqa
                        text: str = '', html: str = '',
                        sender: str = '',
                        files: Optional[Sequence[str]] = None,
                        cc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
                        bcc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
                        exceptions: bool = False):
    """
    Sends email using SendGrid API. Following requirements:
    * pip install sendgrid==6.3.0
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
    :return: Status code 202 if emails were sent successfully
    """
    import sendgrid  # type: ignore  # pylint: disable=import-outside-toplevel
    from sendgrid.helpers.mail import Content, Mail, Attachment  # type: ignore  # pylint: disable=import-outside-toplevel
    from sendgrid import ClickTracking, FileType, FileName, TrackingSettings  # type: ignore  # pylint: disable=import-outside-toplevel
    from sendgrid import Personalization, FileContent, ContentId, Disposition  # type: ignore  # pylint: disable=import-outside-toplevel

    if files is None:
        files = []
    recipients_clean = make_email_recipient_list(recipients)
    cc_recipients_clean = make_email_recipient_list(cc_recipients)
    bcc_recipients_clean = make_email_recipient_list(bcc_recipients)

    try:
        sg = sendgrid.SendGridAPIClient(api_key=settings.EMAIL_SENDGRID_API_KEY)
        from_email = sendgrid.Email(sender or settings.DEFAULT_FROM_EMAIL)
        text_content = Content('text/plain', text) if text else None
        html_content = Content('text/html', html) if html else None

        sg_email_list = []
        to_emails_data = []
        for recipient in recipients_clean:
            sg_email_list.append(sendgrid.To())
            to_emails_data.append(recipient)
        for recipient in cc_recipients_clean:
            sg_email_list.append(sendgrid.Cc())
            to_emails_data.append(recipient)
        for recipient in bcc_recipients_clean:
            sg_email_list.append(sendgrid.Bcc())
            to_emails_data.append(recipient)
        for ix, to_email in enumerate(sg_email_list):
            to_email.email = to_emails_data[ix]
        personalization = Personalization()
        for sg_email in sg_email_list:
            personalization.add_email(sg_email)

        mail = Mail(from_email=from_email, subject=subject, plain_text_content=text_content, html_content=html_content)
        mail.add_personalization(personalization)

        # stop SendGrid from replacing all links in the email
        mail.tracking_settings = TrackingSettings(click_tracking=ClickTracking(enable=False))

        for filename in files:
            with open(filename, 'rb') as fp:
                attachment = Attachment()
                attachment.file_type = FileType("application/octet-stream")
                attachment.file_name = FileName(basename(filename))
                attachment.file_content = FileContent(b64encode(fp.read()).decode())
                attachment.content_id = ContentId(basename(filename))
                attachment.disposition = Disposition("attachment")
                mail.add_attachment(attachment)

        send_time = now()
        res = sg.client.mail.send.post(request_body=mail.get())
        send_dt = (now() - send_time).total_seconds()

        if res.status_code == 202:
            log_event('EMAIL_SENT', data={'time': send_dt, 'to': recipients, 'subject': subject, 'status': res.status_code})
        else:
            log_event('EMAIL_ERROR', data={'time': send_dt, 'to': recipients, 'subject': subject, 'status': res.status_code, 'body': res.body})

    except Exception as e:
        logger.error('Failed to send email (SendGrid) to %s: %s', recipients, e)
        log_event('EMAIL_ERROR', data={'to': recipients, 'subject': subject, 'exception': str(e)})
        if exceptions:
            raise
        return -1

    return res.status_code


def send_email_smtp(recipients: Sequence[Union[str, Tuple[str, str]]], subject: str,  # noqa
                    text: str = '', html: str = '',
                    sender: str = '',
                    files: Optional[Sequence[str]] = None,
                    cc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
                    bcc_recipients: Optional[Sequence[Union[str, Tuple[str, str]]]] = None,
                    exceptions: bool = False):
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
    recipients_clean = make_email_recipient_list(recipients)
    cc_recipients_clean = make_email_recipient_list(cc_recipients)
    bcc_recipients_clean = make_email_recipient_list(bcc_recipients)
    sender_clean = make_email_recipient(sender or settings.DEFAULT_FROM_EMAIL)

    try:
        mail = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=sender_clean,
            to=recipients_clean,
            bcc=bcc_recipients_clean,
            cc=cc_recipients_clean,
        )
        for filename in files:
            mail.attach_file(filename)
        if html:
            mail.attach_alternative(content=html, mimetype='text/html')

        send_time = now()
        mail.send(fail_silently=False)
        send_dt = (now() - send_time).total_seconds()
        log_event('EMAIL_SENT', data={'time': send_dt, 'to': recipients, 'subject': subject})

    except Exception as e:
        logger.error('Failed to send email (SMTP) to %s: %s', recipients, e)
        log_event('EMAIL_ERROR', data={'to': recipients, 'subject': subject, 'exception': str(e)})
        if exceptions:
            raise
        return -1

    return 202
