/* Generation of correlated Gaussian distributed random deviates with modified Box Mulller algorithm */
/*
  Copyright (C) 2009 University of Texas at Austin
  
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
#include <math.h>
#include "bmjgauss.h"

#define IA 16807
#define IM 2147483647 
#define AM (1.0/IM)
#define NTAB 32
#define IQ 127773
#define IR 2836
#define NDIV (1+(IM-1)/NTAB)
#define EPS 1.2e-7
#define RNMX (1.0-EPS)

float rand1_gen(int *idum)
{
/* Minimal random number generator of Park & Miller */
/* with Bays-Durham shuffle and added safeguards */
/* Returns a uniform random deviates between in [0.0,1.0[ (exclusive) */
/* Initial call with idum to any negative integer value */
/* idum must not be altered in successive calls in a sequence */

    int j;
    int k;
    static int iy=0;
    static int iv[NTAB];
    float temp;

    if (*idum <= 0 || !iy) {

	if (-(*idum) < 1) {
	    *idum = 1;
	} else {
	    *idum = -(*idum);
	}

	for (j = NTAB+7; j>=0; j--) {
	    k = (*idum)/IQ;
	    *idum = IA*(*idum-k*IQ)-IR*k;
	    if (*idum < 0) *idum += IM;
	    if (j < NTAB) iv[j] = *idum;
	}

	iy = iv[0];
    }

    k = (*idum)/IQ;
    *idum = IA*(*idum-k*IQ)-IR*k;
    if (*idum < 0) *idum += IM;
    j = iy/NDIV;
    iy = iv[j];
    iv[j] = *idum;

    if ((temp = AM*iy) > RNMX) {
	return RNMX;
    } else {
	return temp;
    }

}

static void gauss_joint(int *iseed, float m1, float m2, float s1, float s2, float r, float *y1, float *y2)
/* Returns two Gaussian positive distributed deviates y1 and y2 with correlation r */
/* using a modified Box Mulller algorithm and rand1_gen(idum) */
/* Expectations = m1,m2 */ 
/* Standard deviation = s1,s2 */
{
 float g1,g2,fac,rsq,v1,v2;
 do
 {
  v1 = 2.0*rand1_gen(&iseed)-1.0;
  v2 = 2.0*rand1_gen(&iseed)-1.0;
  rsq = v1*v1 + v2*v2;
 }
 while (rsq >= 1.0 || rsq == 0.0);
 fac = sqrt(-2.0*log(rsq)/rsq);
 g1 = v1*fac;
 g2 = v2*fac*sqrt(1.0-r*r);
 *y1 = s1*g1 + m1;
 *y2 = (g2+r*g1)*s2 + m2;
 return;
}

void hist_jgauss(float **hist, int n, float r, float m1, float m2, float s1, float s2, int nhalfbin, float dbin, int *iseed) 
{
/* Joint Gaussian distribution histogram */

    int i,i1,i2;
    float x1,x2,norm;        

    norm = 1.0/(dbin*dbin*n);

    for (i = 0; i < n; i++) {

	gauss_joint(&iseed,m1,m2,s1,s2,r,&x1,&x2);

	i1 = floorf((x1-m1)/dbin);
	i2 = floorf((x2-m2)/dbin);

	if ( (fabsf(i1) <= nhalfbin) && (fabsf(i2) <= nhalfbin) ) {
	    hist[i1+nhalfbin+1][i2+nhalfbin+1] += norm;
	}

    }

    return;
}
