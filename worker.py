import os
import redis

from rq import Connection, Worker

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
redis_db = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)

with Connection(redis_db):
    worker = Worker(["default"])
    worker.work()