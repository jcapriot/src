/* Finite-difference modeling/migration: 15- and 45-degree approximation. */
/*
  Copyright (C) 2004 University of Texas at Austin
  
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

#include <math.h>

#include <rsf.h>

#include "ctridiagonal.h"

int main(int argc, char* argv[])
{
    bool inv, hi;
    int nw,nz,nx, iw,ix,iz;
    float dw,dz,dx, vel0, beta, w, w1, w2, omega;
    float complex aa, *cu, *cd, *diag, *offd;
    float **depth, **vel, **voff;
    ctris slv;
    sf_file in, out, velocity;

    sf_init (argc,argv);
    in = sf_input("in");
    out = sf_output("out");

    if (!sf_getbool("inv",&inv)) inv=false;
    /* If y, modeling; if n, migration */
    if (!sf_getfloat("beta",&beta)) beta=1./12.;
    /* "1/6th trick" parameter */
    if (!sf_getbool("hi",&hi)) hi=true;
    /* if y, use 45-degree; n, 15-degree */

    if (NULL != sf_getstring ("velocity")) {
	/* velocity file */
	velocity = sf_input("velocity");
    } else {
	velocity = NULL;
    }

    if (inv) { /* modeling */
	if (SF_FLOAT != sf_gettype(in)) sf_error("Need float input");

	if (!sf_histint(in,"n1",&nz)) sf_error("No n1= in input");
	if (!sf_histint(in,"n2",&nx)) sf_error("No n2= in input");
	if (!sf_histfloat(in,"d1",&dz)) sf_error("No d1= in input");
	if (!sf_histfloat(in,"d2",&dx)) sf_error("No d2= in input");

	if (!sf_getint("nt",&nw)) sf_error("Need nt=");
	/* Length of time axis (for modeling) */
	if (!sf_getfloat("dt",&dw)) sf_error("Need dt=");
	/* Sampling of time axis for modeling) */

	dw = 1./(dw*nw);
	nw = 1+nw/2;

	sf_putint (out,"n2",nw); 
	sf_putfloat (out,"d2",dw);
	sf_putint (out,"n1",nx); 
	sf_putfloat (out,"d1",dx);

	sf_settype(out,SF_COMPLEX);
    } else { /* migration */
	if (SF_COMPLEX != sf_gettype(in)) sf_error("Need complex input");

	if (!sf_histint(in,"n1",&nx)) sf_error("No n1= in input");
	if (!sf_histint(in,"n2",&nw)) sf_error("No n2= in input");
	if (!sf_histfloat(in,"d1",&dx)) sf_error("No d1= in input");
	if (!sf_histfloat(in,"d2",&dw)) sf_error("No d2= in input");

	if (NULL != velocity) {
	    if (!sf_histint(velocity,"n1",&nz)) 
		sf_error("No n1= in velocity");
	    if (!sf_histfloat(velocity,"d1",&dz)) 
		sf_error("No d1= in velocity");
	} else {
	    if (!sf_getint("nz",&nz)) sf_error("Need nz=");
	    /* Length of depth axis (for migration, if no velocity file) */
	    if (!sf_getfloat("dz",&dz)) sf_error("Need dz=");
	    /* Sampling of depth axis (for migration, if no velocity file) */
	}

	sf_putint (out,"n2",nx); 
	sf_putfloat (out,"d2",dx);
	sf_putint (out,"n1",nz); 
	sf_putfloat (out,"d1",dz);

	sf_settype(out,SF_FLOAT);
    }

    vel = sf_floatalloc2(nz,nx);
    voff = sf_floatalloc2(nz,nx-1);

    if (NULL != velocity) {
	sf_floatread (vel[0],nz*nx,velocity);
    } else { /* constant velocity */
	if (!sf_getfloat ("vel", &vel0)) sf_error("Need vel0=");
	/* Constant velocity (if no velocity file) */
	for (ix=0; ix < nx; ix++) {
	    for (iz=0; iz < nz; iz++) {
		vel[ix][iz] = vel0;
	    }
	}
    }

    /* velocity to slowness */
    for (ix=0; ix < nx; ix++) {
	for (iz=0; iz < nz; iz++) {
	    vel[ix][iz] = 2./vel[ix][iz]; 
	    /* 2 from post-stack exploding reflector */
	}
    }
    
    /* symmetrize for stability */
    for (ix=0; ix < nx-1; ix++) {
	for (iz=0; iz < nz; iz++) {
    	    voff[ix][iz] = sqrtf(vel[ix][iz]*vel[ix+1][iz]);
	}
    }

    dw *= 2.*SF_PI*dz;
    dx = 0.25*(dz*dz)/(dx*dx);

    depth = sf_floatalloc2(nz,nx);

    cu = sf_complexalloc (nx);
    cd = sf_complexalloc (nx);
    diag = sf_complexalloc (nx);
    offd = sf_complexalloc (nx-1);

    if (inv) {
	sf_floatread(depth[0],nz*nx,in);
    } else {
	for (ix=0; ix < nx; ix++) {
	    for (iz=0; iz < nz; iz++) {
		depth[ix][iz] = 0.;
	    }
	}
    }
    
    slv = ctridiagonal_init (nx);

    /* d.c. */
    sf_warning("frequency 1 of %d",iw+1, nw);


    for (iw = 1; iw < nw; iw++) {
	sf_warning("frequency %d of %d",iw+1, nw);
	w = dw*iw;

	if (inv) { /* modeling */
	    for (ix=0; ix < nx; ix++) {
		cu[ix] = depth[ix][nz-1];
	    }

	    for (iz = nz-2; iz >= 0; iz--) { /* march up */

		for (ix=0; ix < nx; ix++) {
		    w1 = w*vel[ix][iz];
		    w2 = w*vel[ix][iz+1];
		    omega = 0.5*(w1+w2);
		    aa = beta*omega + I*dx;
		    if (hi) aa += dx*0.5*(1./w1+1./w2);
		    diag[ix] = omega - 2.*aa;
		}           
		for (ix=0; ix < nx-1; ix++) {
		    w1 = w*voff[ix][iz];
		    w2 = w*voff[ix][iz+1];
		    omega = 0.5*(w1+w2);
		    aa = beta*omega + I*dx;
		    if (hi) aa += dx*0.5*(1./w1+1./w2);
		    offd[ix] = aa;
		}
		/* worry about boundary conditions later */
		
		cd[0] = 0.;
		for (ix=1; ix < nx-1; ix++) {
		    cd[ix] = 
			conjf(offd[ix-1])*cu[ix-1] +
			conjf(diag[ix])*cu[ix] +
			conjf(offd[ix])*cu[ix+1];
		}
		cd[nx-1] = 0;

		ctridiagonal_define (slv, diag, offd);
		ctridiagonal_solve (slv, cd);

		for (ix=0; ix < nx; ix++) {
		    w1 = w*vel[ix][iz];
		    w2 = w*vel[ix][iz+1];
		    omega = 2.*(w1+w2-1./(1./w1+1/w2))/3.;
		    cu[ix] = cd[ix] * cexpf(-I*omega) + depth[ix][iz];
		}
	    }

	    sf_complexwrite (cu,nx,out);

	} else { /* migration */

	    sf_complexread (cu,nx,in);

	    for (iz=0; iz < nz-1; iz++) { /* march down */

		for (ix=0; ix < nx; ix++) {
		    w1 = w*vel[ix][iz];
		    w2 = w*vel[ix][iz+1];
		    omega = 2.*(w1+w2-1./(1./w1+1/w2))/3.;

		    depth[ix][iz] += crealf (cu[ix]);
		    cd[ix] = cu[ix] * cexpf(I*omega);
		}

		for (ix=0; ix < nx; ix++) {
		    w1 = w*vel[ix][iz];
		    w2 = w*vel[ix][iz+1];
		    omega = 0.5*(w1+w2);
		    aa = beta*omega - I*dx;
		    if (hi) aa += dx*0.5*(1./w1+1./w2);
		    diag[ix] = omega - 2.*aa;
		}           
		for (ix=0; ix < nx-1; ix++) {
		    w1 = w*voff[ix][iz];
		    w2 = w*voff[ix][iz+1];
		    omega = 0.5*(w1+w2);
		    aa = beta*omega - I*dx;
		    if (hi) aa += dx*0.5*(1./w1+1./w2);
		    offd[ix] = aa;
		}
		/* worry about boundary conditions later */
		
		cu[0] = 0.;
		for (ix=1; ix < nx-1; ix++) {
		    cu[ix] = 
			conjf(offd[ix-1])*cd[ix-1] +
			conjf(diag[ix])*cd[ix] +
			conjf(offd[ix])*cd[ix+1];
		}
		cu[nx-1] = 0;

		ctridiagonal_define (slv, diag, offd);
		ctridiagonal_solve (slv, cu);
	    } /* iz depth loop */

	    for (ix=0; ix < nx; ix++) {
		depth[ix][nz-1] += crealf (cu[ix]);
	    }
	} /* if inverse */
    } /* iw frequency loop */
  
    if (!inv) sf_floatwrite (depth[0],nz*nx,out);

    exit (0);
}

/* 	$Id$	 */
