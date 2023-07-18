import sympy as sym
from sympy.utilities.lambdify import lambdify
from scipy import optimize
from itertools import combinations
import matplotlib.pyplot as plt
import math
import random
import time

def degtorad(deg):
    #dereceden radyana çeviri için fonksiyon
    return deg*math.pi/180


def radtodeg(rad):
    #radyandan dereceye çeviri için fonksiyon
    return rad*180/math.pi

class Plane:
    #2 boyutlu düzlem objesi

    varlst = [] 
    # değişkenlerin tutulduğu liste örnek: [v0,v1,v2,v3]

    cost = 0 
    # hata fonksiyonu

    pts = set() 
    # değişken çiftleri şeklinde noktalar kümesi örnek: {(v0,v1),(v2,v3)}

    lines = set() 
    # nokta çiftleri şeklinde çizgiler kümesi örnek: {((v0,v1),(v4,v5)),((v0,v1),(v2,v3))}

    circles = set()
    # merkez noktası ve yarıçap çiftleri şeklinde daireler kümesi örnek: {((v0,v1),r0),((v2,v3),r1)}

    table = None 
    # optimizasyon sonrası değişkenlerin değerleri buraya kaydedilir

    const = []
    # kısıtlamalar burada derlenir

    start_vals = {}
    #değişkenler için başlangıç değerleri

    bounds = [] 
    #değişkenlerin alabileceği aralık sınırları

    def __init__(self):
        pass

    def add_var(self,x):
        #değişken eklemek için kullanılır, x ile başlangıç değeri belirlenebilir
        length = len(self.varlst)
        self.varlst.append(sym.Symbol(f"v{length}"))
        #değişkenler v0,v1,v2... diye eklenir
        self.start_vals[self.varlst[-1]] = x
        self.bounds.append((0,20))
        return self.varlst[-1]

    def add_custom_sym(self,symbol):
        #ek özel değişken eklemek için kullanılır
        self.varlst.append(symbol)
        self.bounds.append((None,None))

    def add_point(self,x=None,y=None):
        #noktayı ekler ve çıktı olarak verir
        point = (self.add_var(x),self.add_var(y))
        self.pts.add(point)
        return point

    def add_eq(self, t1, t2):
        #eşit olan 2 ifadenin farklarının karelerini hata fonksiyonuna ekler
        self.cost += (t1-t2)**2

    def add_const(self, f):
        #eşitsizlik cinsinde kısıt eklenmesinde kullanılır
        self.const.append({"type":"ineq","fun":f})


    def add_line(self, p1, p2):
        #çizgiyi ekler ve çıktı olarak verir
        l = (p1,p2)
        self.lines.add(l)
        return l

    def add_circle(self, point, radius):
        #daireyi ekler ve çıktı olarak verir
        c = (point,radius)
        self.circles.add(c)
        return c

    def colinear_3pts(self, p1, p2, p3):
        #3 noktanın doğrusal olduğunu hata fonksiyonuna ekler
        x1 = p1[0]    
        x2 = p2[0]    
        x3 = p3[0]    
        y1 = p1[1]    
        y2 = p2[1]    
        y3 = p3[1]    
        self.add_eq(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2),0)

    def vectorize(self,l,p):
        #bir çizginin bir noktasından diğer noktasına vektörünü çıktı olarak verir
        pT = list(set(l) - set([p]))[0]
        return (pT[0] - p[0], pT[1] - p[1])
    
    def dot_product(self,v1,v2):
        #iki vektör arası skaler çarpımı çıktı olarak verir
        return v1[0]*v2[0] + v1[1]*v2[1]

    def vec_length(self, v):
        #bir vektörün uzunluğunu çıktı olarak verir
        return sym.sqrt(v[0]**2 + v[1]**2)

    def line_length(self,l):
        #bir çizginin uzunluğunu çıktı olarak verir
        x1 = l[0][0]    
        x2 = l[1][0]    
        y1 = l[0][1]    
        y2 = l[1][1]    
        return sym.sqrt((x1-x2)**2 + (y1-y2)**2)

    def distance_2pts(self,p1,p2,dist):
        #iki nokta arası uzaklık bilgisini hata fonksiyonuna ekler
        self.add_eq(self.line_length((p1,p2)),dist)

    def eq_distance(self,l1,l2):
        #iki çizginin eşit olduğu bilgisini hata fonksiyonuna ekler
        self.add_eq(self.line_length(l1),self.line_length(l2))

    def line_slope(self,line):
        #bir çizginin eğimini çıktı olarak verir
        p1 = line[0]
        p2 = line[1]
        return (p2[1] - p1[1])/(p2[0] - p1[0])

    def line_point_rel(self,line,pt,positive):
        #bir noktanın bir çizginin sağında veya solunda olduğunu eşitsizlik olarak ekler
        p1,p2 = line[0],line[1]
        x0,y0 = p1[0],p1[1]
        x1,y1 = p2[0],p2[1]
        x,y = pt[0],pt[1]
        con = 0
        if positive:
            con = (y-y0)*(x1-x0) - (x-x0)*(y1-y0) - 1
        else:
            con = -((y-y0)*(x1-x0) - (x-x0)*(y1-y0)) -1
        self.add_const(lambdify([self.varlst],con))


    def perp_lines(self,l1,l2):
        #iki çizgi arasında diklik ilişkisi olduğu bilgisini hata fonksiyonuna ekler
        mult = self.line_slope(l1) * self.line_slope(l2)
        self.add_eq(mult,-1)
    
    def paral_lines(self,l1,l2):
        #iki çizgi arasında paralellik ilişkisi olduğu bilgisini hata fonksiyonuna ekler
        self.add_eq(self.line_slope(l1),self.line_slope(l2))

    def angle_2lines(self, l1, l2, pt):
        #iki çizgi arasındaki açının cosinüsünü çıktı olarak verir
        v1 = self.vectorize(l1,pt)
        v2 = self.vectorize(l2,pt)
        nm = self.dot_product(v1,v2)
        dm = self.vec_length(v1) * self.vec_length(v2)
        return nm/dm

    def angle(self, l1, l2, pt, angle):
        #iki çizgi arasındaki açı bilgisini hata fonksiyonuna ekler
        c = self.angle_2lines(l1,l2,pt)
        a = sym.acos(c)
        self.add_eq(a,angle)

    def polygon_area(self,vertices):
        #bir çokgenin alanını çıktı olarak verir
        psum = 0
        nsum = 0

        for i in range(len(vertices)):
            sindex = (i + 1) % len(vertices)
            prod = vertices[i][0] * vertices[sindex][1]
            psum += prod

        for i in range(len(vertices)):
            sindex = (i + 1) % len(vertices)
            prod = vertices[sindex][0] * vertices[i][1]
            nsum += prod

        return sym.Abs(1/2*(psum - nsum))

    def point_on_circle(self,circle,point):
        #bir noktanın bir daire üzerinde olduğu bilgisini hata fonksiyonuna ekler
        x,y = circle[0][0],circle[0][1]
        x1,y1 = point[0],point[1]
        point_dis = sym.sqrt((x1-x)**2 + (y1-y)**2)
        self.add_eq(circle[1],point_dis)

    def line_tangent_circle(self,c,l):
        #bir çizginin bir daireye teğet geçtiği bilgisini hata fonksiyonuna ekler
        x1,y1,x2,y2 = l[0][0],l[0][1],l[1][0],l[1][1]
        ox,oy = c[0][0],c[0][1]
        x1,x2 = x1-ox,x2-ox
        y1,y2 = y1-oy,y2-oy
        r = c[1]
        dx = x2-x1
        dy = y2-y1
        dr = sym.sqrt(dx**2 + dy**2)
        D = x1*y2 - x2*y1
        delta = (r**2)*(dr**2) - D**2
        self.add_eq(delta,0)

    def area_of_regions(self,regions,value):
        #her biri noktalar listesinden oluşmuş çokgenler listesindeki çokgenlerin,
        #alanlar toplamı bilgisini hata fonksiyonuna ekler

        area = 0
        for r in regions:
            area += self.polygon_area(r)
        self.add_eq(area,value)

    def print_cost(self):
        #hata fonksiyonunu yazdırır
        print(self.cost)

    def turn_lambda(self):
        #hata fonksiyonunu çağrılabilir fonksiyona dönüştürür
        return lambdify([self.varlst],self.cost)

    def solve(self):
        #hata fonksiyonunun minimumunu belirlenen kısıtlamalar içinde bulur
        f = self.turn_lambda()
        ans = None
        bestans = None
        start = time.time()
        while True:
            for i in self.varlst:
                self.start_vals[i] = random.uniform(0,20)
            vals = [self.start_vals[i] for i in self.varlst]
            #değişkenlerin başlangıç değerleri döngünün her turunda rastgele verilir
            ans = optimize.minimize(f,vals,bounds=self.bounds,method="SLSQP",constraints=self.const,
                    options= {"disp":True, "ftol":1e-10,"maxiter":200})
            #verilen başlangıç değerleriyle 200 adımda ulaşılabilen en küçük hata fonksiyonu değeri bulunur
            if ans.fun <= 1e-9:
                #değer 10^-9'a eşit veya ondan küçük olana kadar döngü devam eder
                break
            if bestans == None:
                bestans = ans
            else:
                if bestans.fun > ans.fun:
                    bestans = ans
                    print(bestans.fun)
            #if time.time() - start > 5:
            #    ans = bestans
            #    break


        print(ans)
        lst = ans.x
        self.table = {self.varlst[v]: k for v, k in enumerate(lst)}
        #değişkenlerin değerleri tabloya kaydedilir örnek: {v0:19.5,v1:20.001,x:7}

    def plot(self):
        #bulunan değerlerin oluşturduğu şeklin grafiği çizilir
        t = self.table
        for l in self.lines:
            plt.plot((t[l[0][0]],t[l[1][0]]),(t[l[0][1]],t[l[1][1]]))
        for c in self.circles:
            d = c[1].subs(t)
            circle = plt.Circle((t[c[0][0]], t[c[0][1]]), d, fill=False)
            plt.gca().add_patch(circle)

        plt.show()

