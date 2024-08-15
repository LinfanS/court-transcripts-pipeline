import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

court_case_id = '2014-awf-CODE'

case_details_json = json.dumps({
    "judge_name": "tanweer ikram",
    "verdict": "guilty",
    "sigma_male": True
})

r.hset(f'court-case:{court_case_id}', mapping={
    'case_details': case_details_json
})

contents = r.hgetall(f'court-case:{court_case_id}')

case_details = json.loads(contents['case_details'])

print(case_details['judge_name'])
