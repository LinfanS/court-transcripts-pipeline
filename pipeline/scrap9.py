import json
from ast import literal_eval


my_dict = {None: {None: None}}

print(json.loads(json.dumps(my_dict)))  # {'null': {'null': None}}

print(literal_eval(str(my_dict)))  # {None: {None: None}}
