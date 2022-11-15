import os

from scripts.call import call_nusmv
from scripts.generate_nuxmv import create_nusmv_file
from scripts.iannopollo import not_in_v, renaming
from scripts.readXML import parse_xml, not_same_var


def generate_exp(fi, cs, ncs):
    fi_cs = fi
    fi_not_cs = fi
    for v in cs:
        fi_cs = renaming(fi_cs, v, "_")
    for v in ncs:
        fi_not_cs = renaming(fi_not_cs, v, "_")
    # !fi_cs || !fi_ncs || fi
    return "!(" + fi_cs + ") | !(" + fi_not_cs + ") | (" + fi + ")"


def look_for_dep_var(fi, changing_vars, cs, treated, cv):
    for i in range(len(changing_vars)):
        z = changing_vars[i]
        new_fi = generate_exp(fi, cs, [z])
        call_nusmv("nuxmv_file.smv", new_fi, "counterexample")
        if os.path.exists("../data/counterexample.xml"):
            cs.append(z)
            treated.append(z)
            ncs = not_in_v(cs, cv)
            if ncs:
                other_fi = generate_exp(fi, cs, ncs)
                call_nusmv("nuxmv_file.smv", other_fi, "counterexample")
                if os.path.exists("../data/counterexample.xml"):
                    changing_vars = ob_vars(cs, treated)
                    return look_for_dep_var(fi, changing_vars, cs, treated, cv)
            return cs
    return cs


def partition(fi, cv):
    conjuntos =[]
    cs = []
    treated = []
    for v in cv:
        if not v in treated:
            cs = [v]
            treated.append(v)
            ncs = not_in_v(cs, cv)
            if ncs:
                newfi = generate_exp(fi, cs, ncs)
                call_nusmv("nuxmv_file.smv", newfi, "counterexample")
                if os.path.exists("../data/counterexample.xml"):
                    changing_vars = ob_vars(cs, treated)
                    cs = look_for_dep_var(fi, changing_vars, cs, treated, cv)
                cv = not_in_v(cs, cv)
            conjuntos.append(cs)
            print("New group " + str(cs))
    return conjuntos


def ob_vars(cs, treated):
    counterex = parse_xml("../data/counterexample.xml")
    os.remove("../data/counterexample.xml")
    dvars = list(set(not_same_var(counterex)))
    l3 = not_in_v(cs, dvars)
    l4 = not_in_v(treated, l3)
    return l4

def main():
    ex1 = "(a | ((b & c) & ((a | d) & (!b & !c))))"
    ex1v = ["a", "b", "c", "d"]
    ex2 = "(a | (b & c))"
    ex2v = ["a", "b", "c"]
    ex3 = "((a | b) & ( c | d))"
    create_nusmv_file([], ex1v)
    result = partition(ex3, ex1v)
    os.remove("../smv/nuxmv_file.smv")
    print(str(result))

if __name__ == '__main__':
    # start_time = time.time()
    main()