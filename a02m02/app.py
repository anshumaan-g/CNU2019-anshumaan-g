import time
import os
import redis
from flask import Flask

app = Flask(__name__)
cache = redis.Redis(host='my-redis', port=6379)


def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)


def Fibonacci(n):
    if n<0:
        print("Incorrect input")
    # First Fibonacci number is 0
    elif n==1:
        return 0
    # Second Fibonacci number is 1
    elif n==2:
        return 1
    else:
        return Fibonacci(n-1)+Fibonacci(n-2)

@app.route('/')
def hello():
    count = get_hit_count()
    user = os.environ['USER']
    return "Hello {0}, {1}th fibonacci number is {2}".format(user, count, Fibonacci(count))
