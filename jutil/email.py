import logging


logger = logging.getLogger(__name__)


def send_email(recipients: list, subject: str, text: str, html: str='', sender: str='', files: list=[], exceptions: bool=False):
    """
    :param recipients: List of recipients; or single email (str); or comma-separated email list (str); or list of name-email pairs (e.g. settings.ADMINS)
    :param subject: Subject of the email
    :param text: Body (text)
    :param html: Body (html)
    :param sender: Sender email, or settings.DEFAULT_FROM_EMAIL if missing
    :param files: Paths to files to attach
    :param exceptions: Raise exception if email sending fails
    :return: Status code 202 if all emails were sent successfully, error status code otherwise
    """
    import sendgrid
    from sendgrid.helpers.mail import Content, Mail, Attachment
    from django.conf import settings
    from base64 import b64encode
    from os.path import basename
    from django.utils.timezone import now
    from jutil.logs import log_event

    try:
        # default sender to settings.DEFAULT_FROM_EMAIL
        if not sender:
            sender = settings.DEFAULT_FROM_EMAIL

        # support multiple recipient list styles
        if isinstance(recipients, str):  # allow single email and comma-separated list as input
            recipients = [str(r).strip() for r in recipients.split(',')]

        sg = sendgrid.SendGridAPIClient(apikey=settings.EMAIL_SENDGRID_API_KEY)
        from_email = sendgrid.Email(sender or settings.DEFAULT_FROM_EMAIL)
        content = Content('text/plain', text) if not html else Content('text/html', html)

        attachments = []
        for filename in files:
            with open(filename, 'rb') as fp:
                attachment = Attachment()
                attachment.content = b64encode(fp.read()).decode()
                attachment.type = "application/octet-stream"
                attachment.filename = basename(filename)
                attachment.content_id = basename(filename)
                attachment.disposition = "attachment"
                attachments.append(attachment)
    except Exception as e:
        logger.error(e)
        if exceptions:
            raise
        return -1

    status_codes = []
    for recipient in recipients:
        try:
            t = now()

            to_email = sendgrid.Email()
            if isinstance(recipient, str):
                to_email.email = recipient
            elif (isinstance(recipient, list) or isinstance(recipient, tuple)) and len(recipient) == 2:
                to_email.name = recipient[0]
                to_email.email = recipient[1]
            else:
                raise Exception('Invalid recipient format: {}'.format(recipient))

            mail = Mail(from_email=from_email, subject=subject, to_email=to_email, content=content)
            for attachment in attachments:
                mail.add_attachment(attachment)
            res = sg.client.mail.send.post(request_body=mail.get())

            send_dt = (now()-t).total_seconds()
            if res.status_code == 202:
                log_event('EMAIL_SENT', data={'time': send_dt, 'to': recipient, 'subject': subject, 'status': res.status_code})
            else:
                log_event('EMAIL_ERROR', data={'time': send_dt, 'to': recipient, 'subject': subject, 'status': res.status_code, 'body': res.body})

            status_codes.append(res.status_code)
        except Exception as e:
            logger.error(e)
            if exceptions:
                raise
            status_codes.append(-1)

    for status in status_codes:
        if status != 202:
            return status
    return 202
