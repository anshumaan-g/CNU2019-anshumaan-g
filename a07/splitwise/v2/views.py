import json
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from v2.helpers import *
from v2.models import *
from v2.serializers import *
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import logging
from celery import chord, group
from v2.tasks import *
logger = logging.getLogger(__name__)


def ping(request):
    return HttpResponse(json.dumps({'cn_ad': 'Anshumaan.Parashar'}), content_type="application/json")


def sanitize(request):
    # Erase db
    Categories.objects.all().delete(), User.objects.all().delete()
    Expenses.objects.all().delete(), ExpenseInfo.objects.all().delete()
    Categories.objects.create(name='miscellaneous')
    return HttpResponse('Data refreshed successfully.')


@require_http_methods(['POST'])
def signup(request):
    request_body = json.loads(request.body)
    if not (request_body['email'] or request_body['password']):
        try:
            user = User.objects.create_user(request_body['email'], request_body['email'], request_body['password'])
            return HttpResponse(status=201)
        except Exception:
            return HttpResponse(status=400)
    else:
        HttpResponse(status=400)


@require_http_methods(['POST'])
def login(request):
    request_body = json.loads(request.body)
    username = request_body['email']
    password = request_body['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        auth_login(request, user)
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=401)


@login_required()
@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    return HttpResponse(status=204)


def post_expense(request):
    request_body = json.loads(request.body.decode())
    if 'categories' not in request_body or 'id' not in request_body['categories']:
        return HttpResponse(status=400)
    request_body['categories'] = request_body['categories']['id']
    serializer = ExpenseSerializer(data=request_body)
    if serializer.is_valid():
        expense = serializer.save()
        expense_info_insert(request_body['users'], expense)
        body = {'id': expense.id}
        return HttpResponse(json.dumps({'data': body}), content_type='application/json', status=201)
    return HttpResponse(status=400)


def get_single_expense(request, expense_id):
    expense = Expenses.objects.get(id=expense_id)
    if expense is None:
        return HttpResponse(status=404)
    users = []
    users_raw = ExpenseInfo.objects.filter(expense=expense)
    for user in users_raw:
        users.append({
            'id': user.user.id,
            'owe': user.owe,
            'lend': user.lend
        })
    body = {
        'id': expense.id,
        'categories': {
            'id': expense.categories.id
        },
        'total_amount': expense.total_amount,
        'users': users
    }
    return HttpResponse(json.dumps({'data': body}), content_type='application/json', status=200)


def get_all_expense(request):
    expenses = ExpenseInfo.objects.filter(user_id=request.user.id)
    expenses = [item.expense for item in expenses]
    body = []
    for expense in expenses:
        if expense.deleted:
            continue
        users = []
        users_raw = ExpenseInfo.objects.filter(expense=expense)
        for user in users_raw:
            users.append({
                'id': user.user.id,
                'owe': user.owe,
                'lend': user.lend
            })
        body.append({
            'id': expense.id,
            'categories': {
                'id': expense.categories.id
            },
            'total_amount': expense.total_amount,
            'users': users
        })
    body = {'expenses': body}
    return HttpResponse(json.dumps({'data': body}), content_type='application/json', status=200)


def update_expense(request, expense_id):
    request_body = json.loads(request.body.decode())
    expense = Expenses.objects.get(id=expense_id)
    serializer = UpdateExpenseSerializer(expense, data=request_body, partial=True)
    if not serializer.is_valid():
        return HttpResponse(status=400)
    if 'total_amount' not in request_body:
        request_body['total_amount'] = expense.total_amount
    if 'categories' in request_body and 'id' not in request_body['categories']:
        return HttpResponse(status=400)
    elif 'categories' not in request_body:
        request_body['categories'] = expense.categories.id
    elif 'categories' in request_body:
        request_body['categories'] = request_body['categories']['id']
    if 'description' not in request_body:
        request_body['description'] = expense.description
    Expenses.objects.filter(id=expense_id).update(total_amount=request_body['total_amount'],
                                                  categories=request_body['categories'],
                                                  description=request_body['description'])
    if 'users' in request_body:
        ExpenseInfo.objects.filter(expense=expense_id).delete()
        expense_info_insert(request_body['users'], expense)
    body = {'id': expense.id}
    return HttpResponse(json.dumps({'data': body}), content_type='application/json', status=201)


def delete_expense(request, expense_id):
    Expenses.objects.filter(id=expense_id).update(deleted=1)
    ExpenseInfo.objects.filter(expense=expense_id).delete()
    return HttpResponse(status=200)


@login_required()
@require_http_methods(['GET', 'PUT', 'DELETE'])
def idexpense(request, expense_id):
    if request.method == 'GET':
        return get_single_expense(request, expense_id)
    if request.method == 'PUT':
        return update_expense(request, expense_id)
    if request.method == 'DELETE':
        return delete_expense(request, expense_id)


@login_required()
@require_http_methods(['GET', 'POST'])
def expense(request):
    if request.method == 'POST':
        return post_expense(request)
    elif request.method == 'GET':
        return get_all_expense(request)


def create_category(request):
    request_body = json.loads(request.body.decode())
    serializer = CategorySerializer(data=request_body)
    if not serializer.is_valid():
        return HttpResponse(status=400)
    category = Categories.objects.create(name=request_body['name'])
    body = {'id': category.id}
    return HttpResponse(json.dumps({'data': body}), content_type='application/json', status=201)


def get_all_categories(request):
    categories = Categories.objects.all()
    body = [{'id': category.id, 'name': category.name} for category in categories]
    return HttpResponse(json.dumps({'data': body}), status=201, content_type='application/json')


@require_http_methods(['GET'])
@login_required()
def get_single_category(request, category_id):
    categories = Categories.objects.get(id=category_id)
    body = {'id': categories.id, 'name': categories.name}
    return HttpResponse(json.dumps({'data': body}), status=201, content_type='application/json')


@require_http_methods(['GET', 'POST'])
@login_required()
def category(request):
    if request.method == 'POST':
        return create_category(request)
    elif request.method == 'GET':
        return get_all_categories(request)


@require_http_methods(['GET'])
@login_required()
def get_all_balances(request):
    if request.method == 'GET':
        user_id = request.user.id
        user_x = User.objects.all().order_by('id')[0].id
        if user_id == user_x:
            users = User.objects.all()
            user_balances = [ExpenseInfo.objects.filter(id=user.id).annotate(balance=Sum('owe')-Sum('lend'))[0]
                             for user in users]
            user_balances = [{'id': user.user.id, 'email': user.user.email, 'amount': user.balance}
                             for user in user_balances if user.balance != 0]
            return HttpResponse(json.dumps({'data': {'balances': user_balances}}),
                                status=200, content_type='application/json')
        else:
            balance = ExpenseInfo.objects.filter(id=user_id).annotate(balance=Sum('owe') - Sum('lend'))[0]
            #logger.debug(balance)
            user_balances = [{'id': balance.user.id, 'email': balance.user.email, 'amount': balance.balance}]
            return HttpResponse(json.dumps({'data': {'balances': user_balances}}),
                                status=200, content_type='application/json')


@require_http_methods(['GET'])
@login_required()
def get_specific_balance(request, friend_id):
    if request.method == 'GET':
        if not User.objects.filter(id=friend_id).exists():
            raise Http404()
        user_id = request.user.id
        user_x = User.objects.all().order_by('id')[0].id
        logger.debug(user_x)
        if user_x == user_id:
            balance = ExpenseInfo.objects.filter(id=friend_id).annotate(balance=Sum('owe') - Sum('lend'))[0]
            user_balances = {'id': balance.user.id, 'email': balance.user.email, 'amount': balance.balance}
        elif friend_id == user_x:
            balance = ExpenseInfo.objects.filter(id=user_id).annotate(balance=Sum('lend') - Sum('owe'))[0]
            user_balances = {'id': balance.user.id, 'email': balance.user.email,
                             'amount': balance.balance}
        else:
            user_balances = {'id': friend_id, 'email': User.objects.get(id=friend_id).email, 'amount': 0}
        return HttpResponse(json.dumps({'data': user_balances}), status=200, content_type='application/json')


@require_http_methods(['POST'])
@login_required()
def settle(request):
    request_body = json.loads(request.body.decode())
    if not ('users' in request_body or 'id' in request_body['users']):
        return HttpResponseBadRequest
    user_id = request_body['users']['id']
    request_new = request
    request_new.method = 'GET'
    balance = json.loads(get_specific_balance(request_new, user_id).content)['data']
    if balance["amount"] == 0:
        return HttpResponseBadRequest
    category = Categories.objects.get(name='miscellaneous')
    # Decide who will pay who(m)
    users = [
        {
            'id': user_id,
            'owe': -balance['amount'] if balance["amount"] < 0 else 0,
            'lend': 0 if balance["amount"] < 0 else balance["amount"]
        },
        {
            'id': request.user.id,
            'owe': 0 if balance["amount"] < 0 else balance['amount'],
            'lend': -balance['amount'] if balance['amount'] < 0 else 0
        }
    ]
    balance['amount'] = -balance['amount'] if balance['amount'] < 0 else balance['amount']
    expense = Expenses.objects.create(total_amount=balance['amount'],
                                      categories_id=category.id, description='Settle up')
    expense_info_insert(users, expense)
    return HttpResponse(json.dumps({'data': {'id': expense.id}}), status=201, content_type='application/json')


@require_http_methods(['GET'])
@login_required()
def profile(request):
    balance = ExpenseInfo.objects.filter(id=request.user.id).annotate(balance=Sum('lend') - Sum('owe'))[0]
    body = {
        'outstanding_amount': balance.balance
    }
    return HttpResponse(json.dumps({'data': body}))


@csrf_exempt
def report(request):
    # Chain / Callback to receive result from group
    header = group(active_user.s(), top_categories.s(), top_ower.s(), top_lender.s(), category_wise_expenses.s())
    callback = retrieve.s()
    reports = chord(header)(callback)
    # reports.get()
    res = json.dumps({'data': str(reports)})
    return HttpResponse(res, status=200)


def handler500(request):
    return render(request, '500.html', status=500)
