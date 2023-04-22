import re
import random
orig = r'{test1%0|test2%2|test3}'
# orig = r'{(0703*2,0704*2)*10|(0703*2,0704*2)*15|(0703*2,0704*2)*20}'

if re.match(r'{(.*?)}', orig):
    choices_weighted = [i.split('%') for i in re.findall(r'([^{|}]+)', orig)]
    print(choices_weighted)
    choices = []
    weights = []
    for i in range(len(choices_weighted)):
        choices.append(choices_weighted[i][0])
        if len(choices_weighted[i]) == 2:
            weights.append(int(choices_weighted[i][1]))
        else:
            weights.append(1)
    print(choices)
    print(weights)
    print(random.choices(choices, weights=weights))
else:
    print('Not a weighted random choices.')
