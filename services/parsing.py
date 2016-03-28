__author__ = 'linard_f'


def parse_regie(regie):
    if len(regie) < 10:
        if 'acq' in regie:
            regie = 'ACQ'
        elif 'crd' in regie:
            regie = 'CRD'
        else:
            regie = '-'
    else:
        regie = '-'
    return regie