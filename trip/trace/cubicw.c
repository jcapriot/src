/* Cubic Spline */
/*************************************************************************

Copyright Rice University, 2008.
All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, provided that the above copyright notice(s) and this
permission notice appear in all copies of the Software and that both the
above copyright notice(s) and this permission notice appear in supporting
documentation.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF THIRD PARTY
RIGHTS. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN THIS
NOTICE BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL
DAMAGES, OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.

Except as contained in this notice, the name of a copyright holder shall
not be used in advertising or otherwise to promote the sale, use or other
dealings in this Software without prior written authorization of the
copyright holder.

**************************************************************************/

int cubic_getworksize(int nt) 
/*< Returns workspace size. >*/
{ return 4*nt-3; }

  /* ORIGINAL FORTRAN DOCUMENTATION */
  /* cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc */

  /*     Cubic Spline */
  /*     by Ann Campbell, Summer 1991 */

  /*     function:  This program generates a cubic spline using an */
  /*                input vector and uses it to create an output */
  /*                vector with a specific initial value, sample rate, */
  /*                and number of data points. */

  /* 	the  parameters are: */
  /* 	x1i:	initial x value for input data */
  /* 	hi:	sample rate for input data */
  /* 	vi:	function values for input data */
  /* 	ni:	number of input data points */
  /* 	x1o:	initial x value for output data */
  /* 	ho:	sample rate for output data */
  /* 	vo:	function values as calculated by spline */
  /* 	no:	number of output data points */
  /* 	iend:	type of end condition to be used */
  /* 		iend=1	linear ends, s(1)=s(n)=0 */
  /* 		iend=2	parabolic ends, s(1)=s(2),s(n)=s(n-1) */
  /* 		iend=3  cubic ends, s(1),s(n) are extrapolated */
  /* 			end point */
  /* 	work:	workspace vector */
  /* 	wl:	length of work vector */
  /*       i:      do loop counter */
  /*       first:  first element used in gaussian elimination */
  /*       last:   last element used in gaussian elimination */
  /*       j:      do loop counter, used to hold intermediate values */
  /*       k:      used to hold intermediate values */
  /*       int:    interval of the input values containing a specific */
  /*               output value */
  /*       dv1,dv2:stores intermediate difference calculations */
  /*       dx:     the difference between the x value of a component */
  /*               of the output vector and the x value of the input */
  /*               vector that is closest to it */
  /*       u:      current output x value */

  /*     Error codes: */
  /*     11: incorrect end condition given, choose end condition */
  /*         between 1 and 3' */
  /*     12: not enough input data points, must be > 3 */
  /*     10: not enough workspace, needs 4*ni-3 words */
  /* cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc */
/* 
cubicw.f -- translated by f2c (version 20030320).
You must link the resulting object file with the libraries:
-lf2c -lm   (in that order)
*/

/* consts added 27.02.09 WWS */

/* Subroutine */ 
int cubic_(float const *x1i, 
	   float const *hi, 
	   float const *vi, 
	   int const *ni, 
	   float const * x1o, 
	   float const *ho, 
	   float *vo, 
	   int const *no, 
	   int const *iend, 
	   float *work, 
	   int const *wl)
/*< cubic spline interpolation 
@param[in] nin (int) number of input gridpoints;
@param[in] din (float) step for input grid;
@param[in] oin (float) coordinate of first input sample;
@param[in] vin (float *) input data array;
@param[in] nout (int) number of output gridpoints;
@param[in] dout (float) step for output grid;
@param[in] oout (float) coordinate of first output sample;
@param[out] vout (float *) output data array;
@param[in] iend (int) endpoint code:  
<ol>
<li> iend=1: linear ends, s(1)=s(n)=0 </li>
<li> iend=2: parabolic ends, s(1)=s(2),s(n)=s(n-1) </li>
<li> iend=3 cubic ends, s(1),s(n) are extrapolated </li>
</ol>
@param[in] work (float *) workspace (memory managed externally);
@param[in] wl (int) size of workspace.
*
Code translated from Fortran by f2c, so all args passed by pointer,
whether they are logically const or not.
*
The helper function cubic_getworksize returns the necessary workspace length.
*
\retval 0 normal return
\retval 11 incorrect end condition given (must lie between 1 and 3)
\retval 12 not enough input data points, must be > 3 
\retval 10 not enough workspace, needs 4*ni-3 words 
>*/
{
  /* System generated locals */
  int i__1;

  /* Local variables */
  static int ierr=0;
  static int i__, j, k;
  static float u, dx, dv1, dv2;
  static int int__, last, first;


  /* Parameter adjustments */
  --vi;
  --vo;
  --work;

  /* Function Body */

  /* 	check that an appropriate end condition has been supplied */

  if (*iend < 1 || *iend > 3) {
    ierr=11;
    return ierr;
  }

  /* 	now check if there are enough input data points for the */
  /* 	program to work correctly */

  if (*ni < 3) {
    ierr=12;
    return ierr;
  }

  /* 	then test to see if the length of the workspace vector */
  /* 	is sufficient to calculate the spline. */
  /*       if it is not, set an error code and return to the calling */
  /*       program. */

  if (*wl < 4*(*ni) - 3) {
    ierr=10;
    return ierr;
  }

  /*     to determine the coefficients of the spline, we need */
  /*     estimates of the second derivatives at the different */
  /*     points of the input vector. */
  /*     these estimates are determined by multiplying the inverse */
  /*     of a tridiagonal matrix with the product of another matrix */
  /*     with the input vector. */
  /*     because we know the tridiagonal matrix, rather than its */
  /*     inverse, and the vector produced by the other multiplication, */
  /*     we can use gaussian elimination to solve for the value of */
  /*     the second derivatives. */
  /*     the components of the tridiagonal matrix are stored in */
  /*     work(1..ni-2), work(ni-1..2*ni-4), and work(2*ni-3...3*ni-6). */
  /*     the other vector is stored in work(3*ni-5...4*ni-8). */

  dv1 = (vi[2] - vi[1]) / *hi * 6.f;
  i__1 = *ni - 2;
  for (i__ = 1; i__ <= i__1; ++i__) {
    dv2 = (vi[i__ + 2] - vi[i__ + 1]) / *hi * 6.f;
    work[i__] = *hi;
    work[i__ + *ni - 2] = *hi * 4.f;
    work[i__ + (*ni << 1) - 4] = *hi;
    work[i__ + *ni * 3 - 6] = dv2 - dv1;
    dv1 = dv2;
    /* L10: */
  }
  first = 2;
  last = *ni - 2;
  /* 	adjust for different end conditions */
  /* 	iend = 1:no changes */
  /* 	iend = 2: */
  if (*iend == 2) {
    /* L50: */
    work[*ni - 1] += *hi;
    work[(*ni << 1) - 4] += *hi;
    /* 	iend = 3: */
  } else if (*iend == 3) {
    work[*ni - 1] = *hi * 6;
    work[(*ni << 1) - 3] = 0.f;
    work[*ni - 2] = 0.f;
    work[(*ni << 1) - 4] = *hi * 6;
  }

  /* 	this is where the gaussian elimination is performed */

  i__1 = last;
  for (i__ = first; i__ <= i__1; ++i__) {
    work[i__] /= work[i__ + *ni - 3];
    work[i__ + *ni - 2] -= work[i__] * work[i__ + (*ni << 1) - 5];
    work[i__ + *ni * 3 - 6] -= work[i__] * work[i__ + *ni * 3 - 7];
    /* L110: */
  }
  work[last + *ni * 3 - 6] /= work[last + *ni - 2];
  i__1 = first - 1;
  for (j = last - 1; j >= i__1; --j) {
    work[j + *ni * 3 - 6] = (work[j + *ni * 3 - 6] - work[j + (*ni << 
							       1) - 4] * work[j + *ni * 3 - 5]) / work[j + *ni - 2];
    /* L120: */
  }

  /*     now that the second derivative values have been calculated, */
  /*     they will be stored in work(2..ni-1) */

  i__1 = last;
  for (i__ = first - 1; i__ <= i__1; ++i__) {
    work[i__ + 1] = work[i__ + *ni * 3 - 6];
    /* L130: */
  }

  /* 	the second derivative values must be adjusted for */
  /*       different end conditions, making the second derivative */
  /* 	estimates now occupy work(1...ni). */

  if (*iend == 1) {
    work[1] = 0.f;
    work[*ni] = 0.f;
  } else if (*iend == 2) {
    work[1] = work[2];
    work[*ni] = work[*ni - 1];
  } else if (*iend == 3) {
    work[1] = work[2] * 2 - work[3];
    work[*ni] = work[*ni - 1] * 2 - work[*ni - 2];
  }

  /*     the second derivative values are now used to calculate */
  /*     the coefficients of the spline. */
  /*     the first coefficient(a) is stored in work(ni+1..2*ni-1), */
  /*     the second coefficient(b) is stored in work(2*ni...3*ni-2), */
  /*     and the third coefficient(c) is stored in work(3*ni-1,4*ni-3). */

  i__1 = *ni - 1;
  for (i__ = 1; i__ <= i__1; ++i__) {
    work[i__ + *ni] = (work[i__ + 1] - work[i__]) / (*hi * 6);
    work[i__ + (*ni << 1) - 1] = work[i__] / 2;
    work[i__ + *ni * 3 - 2] = (vi[i__ + 1] - vi[i__]) / *hi - (*hi * 
							       2 * work[i__] + *hi * work[i__ + 1]) / 6;
    /* L200: */
  }

  /*     the spline is now used to produce the output vector. */

  /*     for each component of the output vector, the interval of */
  /*     the input vector which contains this value must first */
  /*     be determined. */
  /*     this interval determines which coefficients of the spline */
  /*     are used, as well as which input data value is added. */

  int__ = 1;
  u = *x1o;
  i__1 = *no;
  for (i__ = 1; i__ <= i__1; ++i__) {
    if (u >= *x1i + (*ni - 1) * *hi) {
      dx = u - (*x1i + (*ni - 2) * *hi);
      vo[i__] = vi[*ni - 1] + dx * (work[(*ni << 2) - 3] + dx * (
								 work[*ni * 3 - 2] + dx * work[(*ni << 1) - 1]));
      u += *ho;
      goto L300;
    }
    if (u >= *x1i + (int__ - 1) * *hi) {
      if (u <= *x1i + int__ * *hi) {
	dx = u - (*x1i + (int__ - 1) * *hi);
	vo[i__] = vi[int__] + dx * (work[int__ + *ni * 3 - 2] + 
				    dx * (work[int__ + (*ni << 1) - 1] + dx * work[
										   int__ + *ni]));
	u += *ho;
	goto L300;
      }
    }
    int__ = 1;
    j = *ni + 1;
  L250:
    k = (int__ + j) / 2;
    if (u < *x1i + (k - 1) * *hi) {
      j = k;
    } else {
      int__ = k;
    }
    if (j > int__ + 1) {
      goto L250;
    } else {
      dx = u - (*x1i + (int__ - 1) * *hi);
      vo[i__] = vi[int__] + dx * (work[int__ + *ni * 3 - 2] + dx * (
								    work[int__ + (*ni << 1) - 1] + dx * work[int__ + *ni])
				  );
      u += *ho;
      goto L300;
    }
  L300:
    ;
  }

  return ierr;
} /* cubic_ */

