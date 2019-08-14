from django.http import Http404
from v2.models import *
from v2.serializers import *


def expense_info_insert(users, expense):
    flag = 1
    total_owe, total_lend = 0, 0
    for user in users:
        user['expense'], user['user'], user_serializer = expense.id, user['id'], ExpenseUserSerializer(data=user)
        flag = flag and user_serializer.is_valid()
        if flag:
            user = user_serializer.save()
            total_owe += user.owe
            total_lend += user.lend
    flag = flag and expense.total_amount > 0 and total_lend == total_owe and total_lend == expense.total_amount
    if not flag:
        expense.delete()
        raise Http404()
