from __future__ import absolute_import, unicode_literals

import json
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import shared_task
from v2.models import *
from django.db.models import Sum, Count
from datetime import datetime, timedelta
import logging
import boto3
import os


logger = logging.getLogger(__name__)


@shared_task
def top_categories():
    cats = Expenses.objects.values('categories').annotate(dcount=Sum('total_amount')).order_by('-dcount')
    # print(cats)
    cats = [cat for cat in cats]
    return cats[:5]


@shared_task
def top_lender():
    user = ExpenseInfo.objects.values('user').annotate(dcount=Sum('lend')).order_by('-dcount')
    # print(user)
    return user[0]


@shared_task
def top_ower():
    user = ExpenseInfo.objects.values('user').annotate(dcount=Sum('owe')).order_by('-dcount')
    # print(user)
    return user[0]


@shared_task
def active_user():
    user = ExpenseInfo.objects.values('user').annotate(dcount=Count('owe')).order_by('-dcount')
    # print(user)
    return user[0]


# @shared_task
# def monthly_category_wise_user_expenses():
#     last_date = datetime.now()
#     first_date = last_date - timedelta(days=180)
#     ExpenseInfo.objects.all().prefetch_related('id__Expenses_set', 'expense_set')
#     for user in users:
#         res = ExpenseInfo.objects.all(user=user).filter(time_stamp__range=(first_date, last_date)).\
#             values('user').values('categories').annotate(expenses=Sum('owe'))
#     # print(res)
#     return res


@shared_task
def category_wise_expenses():
    month_delta = timedelta(days=180)
    today = datetime.now()
    results = []
    for i in range(6):
        expenses = Expenses.objects\
            .filter(time_stamp__range=(today - (i + 1) * month_delta, today - i * month_delta))\
            .values('categories__name').annotate(amount=Sum('total_amount'), count=Count('id'))
        results.append([(expense["categories__name"], float(expense["amount"])) for expense in expenses])
    return json.dumps(dict(category_wise_expenses=results))


@shared_task
def retrieve(request):
    mail(request)
    logger.debug("Kuch to hua hai")


def create_multipart_message(sender: str, recipients: list, title: str,
                             text: str=None, html: str=None, attachments: list=None) -> MIMEMultipart:
    multipart_content_subtype = 'alternative' if text and html else 'mixed'
    msg = MIMEMultipart(multipart_content_subtype)
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    if text:
        part = MIMEText(text, 'plain')
        msg.attach(part)
    if html:
        part = MIMEText(html, 'html')
        msg.attach(part)

    for attachment in attachments or []:
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read())
            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
            msg.attach(part)

    return msg


def send_mail(sender: str, recipients: list, title: str, text: str=None, html: str=None, attachments: list=None) -> dict:
    msg = create_multipart_message(sender, recipients, title, text, html, attachments)
    ses_client = boto3.client('ses')
    return ses_client.send_raw_email(
        Source=sender,
        Destinations=recipients,
        RawMessage={'Data': msg.as_string()}
    )


def mail(results):
    with open("report.txt", "w") as file:
        json.dump(results, file)

    sender = "parashar.anshumaan@codenation.co.in"
    recipients = ["parashar.anshumaan@codenation.co.in"]
    title = "Celery Report"
    body = "Report Attached"
    attachments = ["report.txt"]
    text = ""
    response = send_mail(sender, recipients, title, text, body, attachments)
