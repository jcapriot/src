#!/usr/bin/env python
from __future__ import print_function
import math
 
class InterpText:
    def __init__(self):
        self.xin=[]
        self.yin=[]
    def append(self,x,y):
#        print "append x=" + str(x) + "y=" + str(y)
        self.xin.append(float(x))
        self.yin.append(float(y))
    def read(self,fileName):
#        print "start InterText line loop"
        for self.line in open(fileName):
#            print "line=" + self.line
            tokens=self.line.split()
            self.append(float(tokens[0]),float(tokens[1]))
    def linearInterp(self,x):
        x=float(x)
#        print "compare x=" + str(x) 
#        print "xin[0]=" + xin[0]
        if(x<=self.xin[0]):
            return self.yin[0]
        #print "len(self.xin)=" + str(len(self.xin));
        for i in range(0,len(self.xin)-1):
            #print "test x<=self.xin[i+1]" + str(x) + "<=" + str(self.xin[i+1])
            if(x<=self.xin[i+1]):
                #print "x=" + str(x) + "i=" + str(i)
                return self.yin[i]+ \
                    (x-self.xin[i])*(self.yin[i+1]-self.yin[i])/ \
                      (self.xin[i+1]-self.xin[i])
        return self.yin[-1]

recnoSpn = InterpText()
recnoSpn.read('recnoSpn.txt')

recnoDelrt = InterpText()
recnoDelrt.read('recnoDelrt.txt')

prev_fldr=-9999
fldr_bias=0

for line in open('hdrfile.txt'):
    tokens=line.split()
    tracl =long(tokens[0])
    fldr  =long(tokens[1])
    tracf =long(tokens[2]) 

    # sometimes fldr does not increase.  It seems the field record number
    # is a 3 digit decimal integer.  When it reaches 999 the next fldr is 000.
    # fldr_bias is 1000*(number of times fldr has recycled to 0). 
    if fldr<prev_fldr : 
        fldr_bias += 1000
        
    prev_fldr = fldr

    fldr += fldr_bias
    ep=-999999
    sx    =-999999999
    sy    =-999999999
    gx    =-999999999
    gy    =-999999999
    cdp   =-999999
    offset=-999999
    shot=long(round(recnoSpn.linearInterp(fldr)))
    delrt=long(round(recnoDelrt.linearInterp(fldr)))
    if shot>0 :
        ep=shot
        # use spnCable.txt file to figure out group location
        r_sx=float(6087-ep)*50.0
        r_sy=0

        # trace 48 is the near trace.  trace 1 is far trace
        # first 24 traces are at 100m, last 48 are at 50m
        # cable length is 3600
        # near offset might be 440m and may be 540, 467, 473, 469, 475, or 470
        # I will use 470m  
        # I measure first break at 335 ms.  (335ms-51ms)*1.49 m/ms = 423m 
        # increase by half group and half source arrays lengths (50/2+50/2)
        # and I get 473.  Close to the shot by shot observer notes = 470m.
        # to look at forst breaks on shots with 0 time delay:
        # <allshots.su  suwind key=ep min=3577 max=3607 |  suximage perc=90
 
        nearoff=470
        if tracf > 24 :
            offset= (48-tracf) * 100 + nearoff
        else:
            offset=23*100+nearoff+75+50+50*(23-tracf)
        r_gx=r_sx-offset
        r_gy=0
        
        # cdps should increase in the opposite direction to the fldr
        # that means the last shot collected will map a trace to 101
        # the last shot collected is 511
        # shotx = (6087-511)*50 
        # neartracex = shotx+470
        # smallestmidpointx=  (6087-511)*50.0 + 470.0/2.0
        # cdpinterval is 50 mt.  Half the smallest group interval is 25,
        # but this makes every other cdp zero until you reach the finer
        # group interval on the far traces.
        # cdp = (smallestmidpointx - (r_sx+r_gx)/2.0)/50.0+101       
        smallestmidpointx=  (6087-511)*50 + 470.0/2.0
        cdp = round((smallestmidpointx - (r_sx+r_gx)/2.0)/50.0+101.0)-44

        sx=long(round(r_sx))
        sy=long(round(r_sy))
        gx=long(round(r_gx))
        gy=long(round(r_gy))

    print(str(fldr)  \
         + " " + str(ep)      \
         + " " + str(sx)      \
         + " " + str(sy)      \
         + " " + str(gx)      \
         + " " + str(gy)      \
         + " " + str(cdp)     \
         + " " + str(tracf)   \
         + " " + str(offset)  \
         + " " + str(delrt)) 

 
