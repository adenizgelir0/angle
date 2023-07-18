from z3 import *
import math
set_param('parallel.enable', True)
set_option(precision=5)
set_option(rational_to_decimal=True)
#set_param('parallel.threads.max', 32)
#set_param('sat.local_search_threads', 3)
#set_param('sat.threads', 3)

def Abs(x):
    return If(x >= 0,x,-x)

def degtorad(deg):
    return deg * math.pi/180
def radtodeg(rad):
    return rad * 180/math.pi

class Plane:
    varlst = []
    s=None
    pts = set()
    lines = set()
    def __init__(self):
        self.s = Solver()

    def add_var(self):
        length = len(self.varlst)
        self.varlst.append(Real(f"v{length}"))
        return self.varlst[-1]

    def add_point(self,x=None, y=None):
        point = (self.add_var(),self.add_var())
        for i in self.pts:
            x1,y1 = i[0],i[1]
            x2,y2 = point[0],point[1]
            self.add_rel(Not(And(x1==x2,y1==y2)))
        self.pts.add(point)
        return point

    def add_rel(self,rel):
        self.s.add(rel)

    def solve_for(self,var):
        if self.s.check() == sat:
            print(self.s.model())
            return self.s.model()[var]
        else:
            return None

    def add_line(self,p1, p2):
        l = (p1,p2)
        self.lines.add(l)
        return l

    def colinear_3pts(self,p1,p2,p3):
        x1 = p1[0]
        x2 = p2[0]
        x3 = p3[0]
        y1 = p1[1]
        y2 = p2[1]
        y3 = p3[1]
        self.add_rel(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2) == 0)

    def vectorize(self,l,p):
        pT = list(set(l) - set([p]))[0]
        return (pT[0] - p[0], pT[1] - p[1])

    def dot_product(self,v1,v2):
        return v1[0]*v2[0] + v1[1]*v2[1]

    def vec_length(self, v):
        return v[0]**2 + v[1]**2

    def line_length(self,l):
        x1 = l[0][0]
        x2 = l[1][0]
        y1 = l[0][1]
        y2 = l[1][1]
        return (x1-x2)**2 + (y1-y2)**2

    
    def distance_2pts(self,p1,p2,dist):
        self.add_rel(self.line_length((p1,p2)) == dist**2)

    def eq_distance(self,l1,l2):
        self.add_rel(self.line_length(l1) == self.line_length(l2))

    def line_slope(self,line):
        p1 = line[0]
        p2 = line[1]
        return (p2[1] - p1[1])/(p2[0] - p1[0])

    def perp_lines(self, l1, l2):
        self.add_rel(self.line_slope(l1) * self.line_slope(l2) == -1)

    def paral_lines(self, l1, l2):
        self.add_rel(self.line_slope(l1) == self.line_slope(l2))

    def angle(self, l1, l2, pt, angle):
        v1 = self.vectorize(l1,pt)
        v2 = self.vectorize(l2,pt)
        nm = self.dot_product(v1,v2)
        dm = self.vec_length(v1) * self.vec_length(v2)
        c = math.cos(angle)

        if angle > math.pi/2:
            self.add_rel((nm**2 == dm*c**2, nm < 0))
        elif angle < math.pi/2:
            self.add_rel((nm**2 == dm*c**2, nm > 0))
        else:
            self.perp_lines(l1,l2)
        """
        if angle > math.pi/2:
            self.add_rel(And(Abs((nm**2)/dm - RealVal(c**2)) < 1/1000, nm < 0))
        elif angle < math.pi/2:
            self.add_rel(And(Abs((nm**2)/dm - RealVal(c**2)) < 1/1000, nm > 0))
        else:
            self.perp_lines(l1,l2)
        """

    def eq_angle(self,l11,l12,p1,l21,l22,p2):
        v11 = self.vectorize(l11,p1)
        v12 = self.vectorize(l12,p1)
        nm1 = self.dot_product(v11,v12)
        dm1 = self.vec_length(v11)*self.vec_length(v12)

        v21 = self.vectorize(l21,p2)
        v22 = self.vectorize(l22,p2)
        nm2 = self.dot_product(v21,v22)
        dm2 = self.vec_length(v21)*self.vec_length(v22)
        
        sign_rel = Or(And(dm1>0,dm2>0), And(dm1<0, dm2<0), And(dm1==0, dm2==0))
        angle_rel = (dm2*nm1**2 == dm1*nm2**2)
        self.add_rel(And(angle_rel,sign_rel))

    def trig_3pts(self,p1,p2,p3):
        x1 = p1[0]
        x2 = p2[0]
        x3 = p3[0]
        y1 = p1[1]
        y2 = p2[1]
        y3 = p3[1]
        self.add_rel(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2) != 0)

    def solve_angle(self,l1, l2,pt):
        v1 = self.vectorize(l1,pt)
        v2 = self.vectorize(l2,pt)
        nm = self.dot_product(v1,v2)
        dm = self.vec_length(v1) * self.vec_length(v2)
        q = Real("q")
        a = Bool("a")
        self.add_rel(nm**2 == dm*q)
        self.add_rel((nm>0) == a)
        num = self.solve_for(q)
        if num==None:
            return None
        acute = self.s.model()[a]
        f = None
        if is_rational_value(num):
            f = num.as_fraction()
        else:
            f=num.approx(10).as_fraction()
        if acute:
            return math.acos(abs(float(f.numerator)/float(f.denominator))**0.5)
        return math.acos(-abs(float(f.numerator)/float(f.denominator))**0.5)
        """
        m1 = self.line_slope(l1)
        m2 = self.line_slope(l2)
        q = Real("q")
        self.add_rel((m2 - m1)/(1+m1*m2) == q)
        nm = self.solve_for(q)
        if nm==None:
            return None
        f = nm.as_fraction()
        return math.atan(float(f.numerator)/float(f.denominator))
        """

    def solve_distance(self,p1,p2):
        x1 = p1[0]
        x2 = p2[0]
        y1 = p1[1]
        y2 = p2[1]
        q = Real("q")
        self.add_rel(((x1-x2)**2 + (y1-y2)**2 == q**2, q>=0))
        return self.solve_for(q)


"""
p=Plane()
A = p.add_point()
B = p.add_point()
C = p.add_point()
AB = p.add_line(A,B)
AC = p.add_line(A,C)
BC = p.add_line(B,C)
p.trig_3pts(A,B,C)
p.angle(AB,AC,A,degtorad(35))
p.eq_distance(BC,AC)

s = p.solve_angle(BC,AC,C)
if s is not None:
    print(radtodeg(s))
else:
    print(s)

"""

p=Plane()
A = p.add_point()
B = p.add_point()
C = p.add_point()
D = p.add_point()
E = p.add_point()
AB = p.add_line(A,B)
BC = p.add_line(B,C)
CD = p.add_line(C,D)
DE = p.add_line(D,E)
p.paral_lines(AB,DE)
p.angle(AB,BC,B,degtorad(150))
p.angle(CD,DE,D,degtorad(140))
s = p.solve_angle(BC,CD,C)
if s is not None:
    print(radtodeg(s))
else:
    print(s)

#pt = p.add_point()
#p.add_rel((pt[0] + pt[1] == 1, pt[0] > 1))
#print(p.solve_fr(pt[0]))
