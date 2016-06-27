from __future__ import absolute_import
from gaw.microservice_client import MicroserviceClient
import time

def time_it(fn):
    def wrapper():
        start_time = time.time()
        res = fn()
        end_time = time.time()

        print('time taken:', (end_time - start_time))
        return res

    return wrapper

client = MicroserviceClient('127.0.0.1', 4444, verbose=False)
print(client.test_service.plus(1, 2))

@time_it
def run_many_times():
    for i in range(1000):
        client.test_service.plus(a=1, b=2)

run_many_times()