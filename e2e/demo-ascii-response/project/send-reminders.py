"""Send payment reminder emails for unpaid orders."""

import json
import urllib.request

MAIL_SERVICE = "https://mail.example/v1/send"
TIMEOUT_SECONDS = 30


def post(payload):
    req = urllib.request.Request(
        MAIL_SERVICE,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS)


def send_reminder(customer, order):
    payload = {"to": customer, "template": "payment-reminder", "order": order}
    try:
        post(payload)
    except TimeoutError:
        # The mail service is sometimes slow. Retry once so no reminder
        # is lost.
        post(payload)
