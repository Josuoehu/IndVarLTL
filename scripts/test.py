import os

from scripts.classes import BVarI
from scripts.generate import req_to_string
from scripts.iannopollo import call_aalta_var_list, not_in_v




def check_what_is_wrong(formula, variables):
    # Formula to check which variables are incorrect
    for v in variables:
        n_f = formula + '-> ' + str(v)
        aalta_res, model = call_aalta_var_list('expression.dimacs', n_f)









def principal():
    # os.system("python3 general.py -f ../files/form.txt")
    g1 = [['out1'], ['out2'], ['out3', 'internal1', 'out5']]
    g2 = [['out1', 'out2', 'out3', 'in1', 'in2', 'in3', 'in4', 'in5', 'in6', 'in7', 'internal1', 'out5']]
    a = manage_groups(g1, g2, ['out1', 'out2', 'out3','internal1', 'out5'], ['in1', 'in2', 'in3', 'in4', 'in5', 'in6', 'in7'])
    print(a)

if __name__ == '__main__':
    principal()
