extends RefCounted
## CIEDE2000 adapted to GDScript from gfiumara/CIEDE2000, MIT.
## Pinned upstream af1de42515f3916c16e75980a4635962489af56a; see third_party/CIEDE2000-LICENSE.
## Conversion uses embedded sRGB profiles, D65 2° observer. No physical pigment calibration.
static func _linear(v:float)->float:
	return v/12.92 if v<=0.04045 else pow((v+.055)/1.055,2.4)
static func _f(v:float)->float:
	return pow(v,1.0/3) if v>216.0/24389 else v*(24389.0/27)/116+16.0/116
static func rgb_lab(c:Color)->Array:
	var r:=_linear(c.r);var g:=_linear(c.g);var b:=_linear(c.b)
	var x:=_f((.4124564*r+.3575761*g+.1804375*b)/.95047)
	var y:=_f(.2126729*r+.7151522*g+.0721750*b)
	var z:=_f((.0193339*r+.1191920*g+.9503041*b)/1.08883)
	return [116*y-16,500*(x-y),200*(y-z)]
static func delta_e(lab1:Array,lab2:Array)->float:
	var c1:=sqrt(lab1[1]*lab1[1]+lab1[2]*lab1[2]);var c2:=sqrt(lab2[1]*lab2[1]+lab2[2]*lab2[2]);var cb:float=(c1+c2)/2
	var cb7:=pow(cb,7);var g:=.5*(1-sqrt(cb7/(cb7+6103515625.0)))
	var a1:float=(1+g)*lab1[1];var a2:float=(1+g)*lab2[1]
	var cp1:=sqrt(a1*a1+lab1[2]*lab1[2]);var cp2:=sqrt(a2*a2+lab2[2]*lab2[2])
	var h1:=0.0 if (a1==0 and lab1[2]==0) else fposmod(atan2(lab1[2],a1),TAU)
	var h2:=0.0 if (a2==0 and lab2[2]==0) else fposmod(atan2(lab2[2],a2),TAU)
	var dl:float=lab2[0]-lab1[0];var dc:=cp2-cp1;var dh:=h2-h1
	if cp1*cp2==0:dh=0
	elif dh>PI:dh-=TAU
	elif dh < -PI:dh+=TAU
	var dhp:=2*sqrt(cp1*cp2)*sin(dh/2);var lp:float=(lab1[0]+lab2[0])/2;var cp:float=(cp1+cp2)/2
	var hp:=h1+h2
	if cp1*cp2!=0:
		if absf(h1-h2)<=PI:hp/=2
		elif hp<TAU:hp=(hp+TAU)/2
		else:hp=(hp-TAU)/2
	var t:=1-.17*cos(hp-deg_to_rad(30))+.24*cos(2*hp)+.32*cos(3*hp+deg_to_rad(6))-.20*cos(4*hp-deg_to_rad(63))
	var theta:=deg_to_rad(30)*exp(-pow((hp-deg_to_rad(275))/deg_to_rad(25),2));var cp7:=pow(cp,7)
	var rc:=2*sqrt(cp7/(cp7+6103515625.0));var sl:=1+.015*pow(lp-50,2)/sqrt(20+pow(lp-50,2));var sc:=1+.045*cp;var sh:=1+.015*cp*t
	return sqrt(maxf(0,pow(dl/sl,2)+pow(dc/sc,2)+pow(dhp/sh,2)-sin(2*theta)*rc*(dc/sc)*(dhp/sh)))
