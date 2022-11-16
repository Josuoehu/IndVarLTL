import os, stat


def call_get_path(is_linux, is_nusmv):
    if is_nusmv:
        if not is_linux:
            calling = './get_path.sh /Users NuSMV'
        else:
            calling = './get_path.sh /home NuSMV'
    else:
        # Falta implementar
        calling = ''
    os.system(calling)


def call_nusmv_bounded(script, expression, out_name, bound):
    command = '\'go_bmc;check_ltlspec_bmc -p \"' + expression + '\" -k ' + str(bound) + '; show_traces -p 4 -o ../data/' + out_name\
              + '.xml;quit\''
    calling = './call_nusmv.sh ' + command + ' ' + script
    os.system(calling)


def call_nusmv(script, expression, out_name):
    command = '\'go;check_ltlspec -p \"' + expression + '\"; show_traces -p 4 -o ../data/' + out_name\
              + '.xml;quit\''
    calling = './call_nusmv.sh ' + command + ' ' + script
    os.system(calling)


def call_aalta(input_file, out_name):
    command = '../files/' + input_file
    calling = './call_aalta.sh ' + command + ' ../data/result.txt'
    os.system(calling)


def main():
    # call_nusmv("nuxmv_file.smv", "G(!w)", "counterexample")
    call_aalta('exten.dimacs', 'res_exten.txt')
    # '!(F(STATE=STATE_SET_COOKING_TEMP) & X(STATE=STATE_INIT))'
    # '!(F((STATE=STATE_SET_COOKING_TEMP)&(in_LCD=LCD_SELECT)) & X(STATE=STATE_SET_COOKING_TIME))'
    # !F(STATE=STATE_SET_COOKING_TIME & in_LCD = LCD_UP & X(var_desiredTime=var_desiredTimePrev + 10.0))

if __name__ == '__main__':
    main()