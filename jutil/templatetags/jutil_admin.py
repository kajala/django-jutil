import json
from gettext import gettext
from django.contrib.admin.models import LogEntry
from django.utils.text import get_text_list
from django.template.defaultfilters import register


@register.filter
def format_change_message_ex(action: LogEntry) -> str:
    """
    Formats extended admin change message which contains new values as well.
    See jutil.admin.ModelAdminBase.
    """
    if action.change_message and action.change_message[0] == "[":
        try:
            change_message = json.loads(action.change_message)
        except json.JSONDecodeError:
            return action.change_message
        messages = []
        for sub_message in change_message:
            if "added" in sub_message:
                if sub_message["added"]:
                    sub_message["added"]["name"] = gettext(sub_message["added"]["name"])
                    messages.append(gettext("Added {name} “{object}”.").format(**sub_message["added"]))
                    if "values" in sub_message["added"]:
                        messages.append("Initial values: {}.".format(list(sub_message["added"]["values"].values())))
                    if "ip" in sub_message["added"]:
                        messages.append("User IP: {}.".format(sub_message["added"]["ip"]))
                else:
                    messages.append(gettext("Added."))

            elif "changed" in sub_message:
                sub_message["changed"]["fields"] = get_text_list(
                    [gettext(field_name) for field_name in sub_message["changed"]["fields"]],
                    gettext("and"),
                )
                if "name" in sub_message["changed"]:
                    sub_message["changed"]["name"] = gettext(sub_message["changed"]["name"])
                    messages.append(gettext("Changed {fields} for {name} “{object}”.").format(**sub_message["changed"]))
                else:
                    messages.append(gettext("Changed {fields}.").format(**sub_message["changed"]))
                if "values" in sub_message["changed"]:
                    messages.append("New values: {}.".format(list(sub_message["changed"]["values"].values())))
                if "ip" in sub_message["changed"]:
                    messages.append("User IP: {}.".format(sub_message["changed"]["ip"]))

            elif "deleted" in sub_message:
                sub_message["deleted"]["name"] = gettext(sub_message["deleted"]["name"])
                messages.append(gettext("Deleted {name} “{object}”.").format(**sub_message["deleted"]))
                if sub_message["deleted"] and "ip" in sub_message["deleted"]:
                    messages.append("User IP: {}.".format(sub_message["deleted"]["ip"]))

        change_message = " ".join(msg[0].upper() + msg[1:] for msg in messages)
        return change_message or gettext("No fields changed.")
    return action.change_message
