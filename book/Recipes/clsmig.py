import os

# prepare for shot-profile migration
def sppre(ngroup):

    allsou = ['_s%03d.rsf' % x for x in range(ngroup)]
    allrec = ['_r%03d.rsf' % x for x in range(ngroup)]
    alljmg = ['_j%03d.rsf' % x for x in range(ngroup)]
    
    silent = ' -s '
    #silent = ' -Q '
    
    for sou in allsou:
        mycom = 'scons' + silent + sou
        os.system(mycom)
        
    for rec in allrec:
        mycom = 'scons' + silent + rec
        os.system(mycom)
            
    for jmg in alljmg:
        mycom = 'scons -n -Q ' + jmg
        os.system(mycom)

# prepare for survey sinking migration
def sgpre(ngroup):

    alldat = ['_e%03d.rsf' % x for x in range(ngroup)]
    allimg = ['_i%03d.rsf' % x for x in range(ngroup)]
    
    silent = ' -s '
    #silent = ' -Q '

    for dat in alldat:
        mycom = 'scons' + silent + dat
        os.system(mycom)

    for img in allimg:
        mycom = 'scons -n -Q ' + img
        os.system(mycom)
