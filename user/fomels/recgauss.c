/* Gaussian smoothing by recursive filtering */
/*
  Copyright (C) 2007 University of Texas at Austin
  
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/
#include <rsf.h>

#include "recgauss.h"

#define BAND 4

static sf_bands band;

void recgauss_init(int nx     /* trace length */, 
		   float rect /* smoothing length */)
/*< initialize >*/
{
    float diag, offd[BAND];

    /* convert length into Gaussian factor */
    rect = (rect*rect-1.)/12.;
    
    diag = 1. + rect*(205./72. + 
		      rect*(5.6875 + 
			    rect*(6.25 + 35.*rect/12.)));
    offd[0] = -rect*(1.6 + 
		     rect*(61./15. + 
			   rect*(29./6. + 7.*rect/3.)));
    offd[1] = rect*(0.2 + 
		    rect*(169./120. + 
			  rect*(13./6. + 7*rect/6.)));
    offd[2] = -rect*(8./315. + 
		     rect*(0.2 + 
			   rect*(0.5 + rect/3.)));
    offd[3] = rect*(1./560. + 
		    rect*(7./480. + 
			  rect*(1. + rect)/24.));
    
    band = sf_banded_init (nx,BAND);
    sf_banded_const_define (band,diag,offd);
}

void recgauss(float *data)
/*< smooth (in place) >*/
{
    sf_banded_solve (band,data);
}

void recgauss_close(void)
/*< free allocated storage >*/
{
    sf_banded_close (band);
}
