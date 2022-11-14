def req_to_string(req):
    # From a binary tree of a requirement returns it on a string

    if not (type(req) == str):
        if len(req) == 2:
            return req[0] + '(' + req_to_string(req[1]) + ')'
        elif len(req) == 3:
            if req[0] == '==':
                return '(' + req_to_string(req[1]) + '=' + req_to_string(req[2]) + ')'
            if req[0] == '-':
                return '(' + req_to_string(req[1]) + ' - ' + req_to_string(req[2]) + ')'
            return '(' + req_to_string(req[1]) + req[0] + req_to_string(req[2]) + ')'
        else:
            return req[0]
    else:
        return req


def req_to_string_2(g):
    left = g[0].replace("&&", "&").replace("||", "|")
    right = g[1].replace("&&", "&").replace("||", "|")
    return "((" + left + ") -> " + right + ")"


def take_negations(req):
    # From a binary makes the treatment for the negations
    # If there is !(!X) then X
    # If there is !(A && B) then !A || !B
    # If there is !(A || B) then !A && !B

    if not(type(req) == str):
        # If '!' it is len(req) == 2
        if req[0] == '!':
            if req[1][0] == '!':
                req = take_negations(req[1][1])
                return req
            elif req[1][0] == '|':
                req = ['&', ['!', take_negations(req[1][1])], ['!', take_negations(req[1][2])]]
                return req
            elif req[1][0] == '&':
                req = ['|', ['!', take_negations(req[1][1])], ['!', take_negations(req[1][2])]]
                return req
            else:
                return req
        # if not, len(req) == 3
        else:
            req = [req[0], take_negations(req[1]), take_negations(req[2])]
            return req
    else:
        return req


def no_higher_and(req):
    # No higher ands than ors in the binary tree
    # If A && (B || C) then (A && B) || (A && C)

    if not(type(req) == str):
        if not(type(req) == tuple):
            if len(req) == 3:
                if req[0] == '&':
                    if req[1][0] == '|':
                        req1 = ['&', req[2], req[1][1]]
                        req2 = ['&', req[2], req[1][2]]
                        req = ['|', no_higher_and(req1), no_higher_and(req2)]
                        return req
                    elif req[2][0] == '|':
                        req1 = ['&', req[1], req[2][1]]
                        req2 = ['&', req[1], req[2][2]]
                        req = ['|', no_higher_and(req1), no_higher_and(req2)]
                        return req
                    else:
                        req = ['&', no_higher_and(req[1]), no_higher_and(req[2])]
                        return req
                else:
                    req = [req[0], no_higher_and(req[1]), no_higher_and(req[2])]
                    return req

            # if not, len(req) == 2
            else:
                req = [req[0], no_higher_and(req[1])]
                return req
        else:
            req = ['->', no_higher_and(req[0]), no_higher_and(req[1])]
            return req
    else:
        return req

def main():
    a = ("a", "b")
    print(type(a))

    result = M()
    r0 = take_negations(result)
    print('r0: ' + str(r0))
    r1 = no_higher_and(r0)
    print('r1: ' + str(r1))
    print(req_to_string(r1))
    return r1

if __name__ == '__main__':
    main()