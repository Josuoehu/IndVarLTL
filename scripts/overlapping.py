from typing import re

from generate import req_to_string
from call import call_nusmv
import os


def check_overlapping(req_list):
    for i in range(len(req_list)):
        for j in range(i+1, len(req_list)):
            r1A = req_to_string(req_list[i][0])
            r2A = req_to_string(req_list[j][0])
            # ll1 = "G(!(" + r1A + ")|(" + r2A + "))"
            # ll1 = "((!(" + r1A + ")|(" + r2A + "))|(!(" + r2A + ")|(" + r1A + ")))"
            ll1 = "(" + r1A + ") -> (" + r2A + ")"
            r1onr2 = False
            r2onr1 = False
            if os.path.exists("../smv/nuxmv_file_prev.smv"):
                print(ll1)
                # call_nusmv("nuxmv_file_prev.smv", ll1, "over", 10)
                call_nusmv("nuxmv_file_prev.smv", ll1, "over")
                if not(os.path.exists("../data/over.xml")):
                    r1onr2 = True
                    # # DEVUELVE TRUE
                    # r1B = req_to_string(req_list[i][1])
                    # r2B = req_to_string(req_list[j][1])
                    # # ll2 = "!F(" + r1B + "&" + r2B + ")"
                    # ll2 = "!(" + r1B + "&" + r2B + ")"
                    # print(ll2)
                    # call_nusmv("nuxmv_file_prev.smv", ll2, "over")
                    # if not (os.path.exists("../data/over.xml")):
                    #     #DEVUELVE TRUE, SON INCOMPATIBLES
                    #     return [True, r1A, r1B, r2A, r2B, "inconsistent"]
                    # else:
                    #     return [True, r1A, r1B, r2A, r2B, "overlapping"]
                if not r1onr2:
                    os.remove("../data/over.xml")
                ll2 = "(" + r2A + ") -> (" + r1A + ")"
                # call_nusmv("nuxmv_file_prev.smv", ll2, "over", 10)
                call_nusmv("nuxmv_file_prev.smv", ll2, "over")
                if not (os.path.exists("../data/over.xml")):
                    r2onr1 = True
                if r1onr2 or r2onr1:
                    r1B = req_to_string(req_list[i][1])
                    r2B = req_to_string(req_list[j][1])
                    # ll2 = "!F(" + r1B + "&" + r2B + ")"
                    ll3 = "!(" + r1B + "&" + r2B + ")"
                    print(ll2)
                    # call_nusmv("nuxmv_file_prev.smv", ll3, "over", 10)
                    call_nusmv("nuxmv_file_prev.smv", ll3, "over")
                    if not (os.path.exists("../data/over.xml")):
                        # DEVUELVE TRUE, SON INCOMPATIBLES
                        return [True, r1A, r1B, r2A, r2B]
                os.remove("../data/over.xml")
    return [False, None, None, None, None]

def main():
    r = [[['&', 'in_right_hand', 'in_left_hand'], 'out_lathe'], [['&', ['!', 'in_right_hand'], 'in_left_hand'], ['!', 'out_lathe']], [['&', 'in_right_hand', ['!', 'in_left_hand']], ['!', 'out_lathe']], [['&', ['!', 'in_right_hand'], ['!', 'in_left_hand']], ['!', 'out_lathe']]]
    check_overlapping(r)

if __name__ == '__main__':
    main()
