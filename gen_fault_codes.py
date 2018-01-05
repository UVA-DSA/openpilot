import os
import numpy as np


def gen_add_code(trigger, t1, t2, variable, stuck_value):
    assert(len(variable) == len(stuck_value))
    code = 'if %s>=%s and %s<=%s:' % \
            (trigger, t1, trigger, t2)
    for v, s in zip(variable, stuck_value):
        l = '//%s+=%s' % (v,s)
        code = code + l
    return code

def write_to_file(fileName, code, param, exp_name, target_file, faultLoc):
    out_file = fileName+'.txt'
    param_file = fileName+'_params.csv'

    with open(out_file, 'w') as outfile:
        print out_file
        outfile.write('title:' + exp_name + '\n')
        outfile.write('location//' + target_file+ '//'+faultLoc + '\n')
        for i, line in enumerate(code):
            outfile.write('fault ' + str(i) + '//' + line + '\n')

    with open(param_file, 'w') as outfile:
        for i, line in enumerate(param):
            outfile.write(str(i) + ',' + line + '\n')

def gen_rel_dist_fault_plant():
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#HOOK#'
    trigger = 'frameIdx'
    code = []
    param = []
    variable = ['d_rel']
    delta = np.arange(10,201,10)
    for d in delta:
      for t1 in [500, 1000, 1500, 2000]:
        for dt in np.arange(100, 1001, 100):
          t2 = t1+dt
          code.append(gen_add_code(trigger, t1, t2, variable, [d]))
          param.append(','.join(['relative distance',str(t1),str(dt),str(d)]))

    write_to_file('dRelPlant', code, param, 'rel_dist_fault_plant', fileLoc, faultLoc)


gen_rel_dist_fault_plant()
