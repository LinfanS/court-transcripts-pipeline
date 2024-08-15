import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

r.hset('user-session:123', mapping={
    'name': 'John',
    "surname": 'Smith',
    "company": 'Redis',
    "age": 29
})

contents = r.hgetall('user-session:123')

print(contents)