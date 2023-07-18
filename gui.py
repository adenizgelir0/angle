from opt import *
import sympy as sym
import pygame
import networkx as nx
import numpy as np
import math
import subprocess

def pt_in(pt, poly):                                                                                              
    #bir noktanın bir çokgenin içinde olup olmadığını bulan fonksiyon
    #raycasting ile çalışır
    testX, testY = pt                                                                                                    
    last = poly[-1]                                                                                                      
    answer = False                                                                                                       
    for now in poly:                                                                                                     
        nowX, nowY = now                                                                                                 
        lastX, lastY = last                                                                                              
        if (nowY > testY) != (lastY > testY) and (testX < (lastX - nowX) * (testY - nowY)/(lastY - nowY) + nowX):        
            answer = not answer                                                                                          
        last = now                                                                                                       
    return answer

def degtorad(deg):
    #dereceden radyana dönüşüm yapar
    return deg*math.pi/180

pygame.init()
win = pygame.display.set_mode((900,700))
win.fill((255,255,255))

answers = None
#cevaplar bulunduğunda buraya kaydedilir

font = pygame.font.SysFont(None, 24)
run = True
#ana döngünün devamını belirler False olursa döngü durur

pt_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
#noktalara verilen isimler için liste

points = {}
#noktalar listesi örnek: {"A":(100,150),"B":(200,125)}

lines = set()
#çizgiler listesi örnek {("A","B"),("B","C")}

circles = set()
#daireler listesi


selected_c = {}
#o anda seçili olan daireler ve hangi noktalarından seçildiklerinin tablosu

selected = set()
#o anda seçilmiş olan çizgi ve nokta grubu

selected_regs = []
#o anda seçilmiş olan bölgeler listesi

buttons = []
#o anda ekranda olan düğmeler listesi

button_count = 0
#ekrandaki düğme sayısı

button_funct = set()
#ekrandaki düğmelerin işlevleri

button_texts = {
        "del":font.render("seçilenleri sil",True,(255,0,0)),
        "line":font.render("çizgi oluştur",True,(0,0,0)),
        "parallel":font.render("paralel yap",True,(0,0,0)),
        "perp":font.render("dik yap",True,(0,0,0)),
        "colinear":font.render("doğrusal yap",True,(0,0,0)),
        "eqdis":font.render("eş uzunluk",True,(0,0,0)),
        "circle":font.render("daire oluştur",True,(0,0,0)),
        "circlept":font.render("nokta oluştur",True,(0,0,0)),
        "circletan":font.render("çembere teğet",True,(0,0,0)),
        }
#düğme oluşturulduğunda yazıları

input_boxes = []
#ekrandaki yazı kutularının listesi

input_boxes_state = {}
#ekrandaki yazı kutularının durumları, aktiflik vs.

input_box_texts = {
    "rad":"radyan cinsinden açı gir",
    "dis":"uzunluk gir",
    "deg":"derece cinsinden açı gir",
    "query":"sorulan ifadeyi gir",
    "area":"seçilen alanın değerini gir"
}
#yazı kutularındaki başlangıç yazıları


log_texts = [
    'sol tuşla nokta ekle veya şekilleri seç, sağdaki kutudan seçenekleri ayarla, esc ile seçimi kaldır.',
    'F1 ile çizimi bitir.'
        ]
#ekrandaki başlangıç yazıları


def line_pt_rel(l,p):
    #bir noktanın bir çizginin sağında veya solunda olduğunu çıktı olarak verir
    p0,p1 = l[0],l[1]
    x,y = p[0],p[1]
    return 0 < (y-p0[1])*(p1[0]-p0[0]) - (x-p0[0])*(p1[1] - p0[1])
    

def point_inline(l,p):
    #bir noktanın bir çizgi üzerinde olup olmadığını çıktı olarak verir
    x1,y1 = l[0][0],l[0][1]
    x2,y2 = l[1][0],l[1][1]
    mid = ((x1+x2)/2, (y1+y2)/2)
    dis_mid = ((mid[0] - p[0])**2 + (mid[1] - p[1])**2)**0.5
    length = ((x1-x2)**2 + (y1-y2)**2)**0.5
    #yöntem olarak önce noktanın çizgiyi çap olarak alan bir dairenin içinde olup olmadığı kontrol edilir
    #sonra çizginin doğruya uzaklığının belirli bir aralıkta olup olmadığına göre çıktı verilir
    if dis_mid > length/2:
        return False
    x0,y0 = p[0],p[1]
    nm = abs((x2-x1)*(y1-y0) - (x1-x0)*(y2-y1))
    dm = ((x2-x1)**2 + (y2-y1)**2)**0.5
    distance = nm/dm
    if distance <= 5:
        return True
    return False



def add_button(func):
    #düğme ekler
    global button_count
    global buttons
    global button_texts
    global button_funct
    if func not in button_funct:
        btn = pygame.draw.rect(win,(0,0,0),(630,20+40*button_count,250,30),2)
        win.blit(button_texts[func],(635,25+40*button_count))
        button_count+=1
        buttons.append((btn,func))
        button_funct.add(func)

def add_input_box(func):
    #yazı kutusu ekler
    global input_boxes
    global input_box_texts
    global input_boxes_state
    if func not in input_boxes_state:
        input_boxes.append(func)
        for c in const:
            if c["targets"] == selected and c["type"] == func:
                input_boxes_state[func] = {"active":False, "text":c["value"], "rect":None}
                return None
        input_boxes_state[func] = {"active":False, "text":input_box_texts[func], "rect":None}



def draw_input_boxes():
    #yazı kutularını çizer
    global input_boxes
    global input_boxes_state
    global button_count
    c = button_count
    for box in input_boxes:
        state = input_boxes_state[box]
        f = None
        if state["active"]:
            f = font.render(state["text"],True,(0,0,0))
        else:
            f = font.render(state["text"],True,(134,136,138))

        r = pygame.draw.rect(win,(0,0,0),(630,20+40*c,250,30),2)
        input_boxes_state[box]["rect"] = r
        win.blit(f,(635,25+40*c))
        c+=1



def print_logs():
    #kullanıcıya gösterilmesi istenilen yazıları yazdırır
    global log_texts
    x,y = 20,530
    for i in log_texts:
        t = font.render(i,True,(0,0,0))
        win.blit(t,(x,y))
        y+=20

def add_log(st):
    #yazılacak yeni satır ekler
    global log_texts
    if len(log_texts) == 8:
        log_texts.pop(0)
    log_texts.append(st)

def area(p):
    #bir çokgenin alanını hesaplar
    return 0.5 * abs(sum(x0*y1 - x1*y0
                         for ((x0, y0), (x1, y1)) in segments(p)))

def segments(p):
    return zip(p, p[1:] + [p[0]])

const = []
#kısıtlamalar buraya kaydedilir örnek:
#[{"type":"perp","targets":{("A","B"),("B","C")}}, {"type":"colinear":"targets":{"A","B","D"}]

forced = False
#ana döngünün bitirilmesi emrinin kullanıcı mı yoksa program mı tarafından verildiğinin kaydını tutar


while run:
    #ana döngü
    G = nx.Graph()
    G.add_nodes_from([i for i in points])
    G.add_edges_from(list(lines))
    regions = list(nx.cycle_basis(G))
    regpts = []
    for r in regions:
        pts = []
        for pt in r:
            pts.append(points[pt])
        regpts.append({"pts":pts,"pnames":r})
    #o andaki çizgiler ve noktalar listesi bir çizgeye dönüştürülür ve tekrarsız döngülerinden bölgelere ayrılır
    regpts = sorted(regpts, key=lambda x:area(x["pts"]))
    #bölgeler alanlarına göre küçükten büyüğe sıralanır

    buttons = []
    button_count = 0
    button_funct = set()
    #düğmeler ile ilgili ayarlar başlangıç konumlarına getirilir

    win.fill((255,255,255))
    #ekran beyaza boyanır

    for r in selected_regs:
        pygame.draw.polygon(win,(0,0,255),r["pts"],width=0)
    #seçilmiş bölge alanları maviye boyanır

    drawingrect = pygame.draw.rect(win, (0,0,0), (10,10,600,500),2)
    #çizim penceresi oluşturulur

    pygame.draw.rect(win, (0,0,0), (10,520,880,170),2)
    #yazı penceresi oluşturulur

    optionrect = pygame.draw.rect(win, (0,0,0), (620,10,270,500),2)
    #seçenek penceresi oluşturulur

    print_logs()
    #o anda yazı listesinde bulunan yazılar yazdırılır
    
    if len(selected) == 0 and answers == None and selected_regs==[]:
        #eğer seçilen öğe yok ise yazı kutuları otomatik silinir
        input_boxes = []
        input_boxes_state = {}

    p_count,l_count,c_count = 0,0,0
    for s in list(selected):
        if type(s) is tuple:
            l_count+=1
        elif type(s) is str:
            p_count+=1
    for c in selected_c:
        c_count+=1
    #nokta,çizgi ve dairelerden kaç tane seçildiği kaydedilir

    if answers != None:
        #kullanıcı çizimi bitirmesi sonrası soru ifadesi yazı kutusu oluşturulur
        add_input_box("query")

    if l_count > 0 or p_count > 0:
        #eğer seçilen çizgi ve noktalar var ise seçilen öğeleri sil düğmesi eklenir
        add_button("del")

    if l_count == 0 and p_count==2:
        #sadece iki nokta seçilmişse çizgi oluşturma düğmesi eklenir
        t = tuple(selected)
        if t in lines or t[::-1] in lines:
            pass
        else:
            add_button("line")

    if l_count==2 and p_count==0:
        #sadece iki çizgi seçilmişse paralellik düğmesi eklenir
        already = False
        for c in const:
            if c["type"] == "parallel" and selected==c["targets"]:
                already = True
                break
        if not already:
            add_button("parallel")

    if l_count==1 and p_count==1:
        #bir nokta ve çizgi seçilmişse daire oluşturma düğmesi eklenir
        pt = None
        line = None
        for s in list(selected):
            if type(s) == tuple:
                line = s
            elif type(s) == str:
                pt = s
        if pt in set(line):
            add_button("circle")

    if l_count==2 and p_count==0:
        #sadece iki çizgi seçilmişse diklik düğmesi eklenir
        already = False
        for c in const:
            if c["type"] == "perp" and selected==c["targets"]:
                already = True
                break
        if not already:
            add_button("perp")

    if l_count==2 and p_count==0:
        #sadece iki çizgi seçilmişse eş uzunluk düğmesi eklenir
        already = False
        for c in const:
            if c["type"] == "eqdis" and selected==c["targets"]:
                already = True
                break
        if not already:
            add_button("eqdis")

    if l_count==0 and p_count==3:
        #üç nokta seçilmişse doğrusallık düğmesi eklenir
        already = False
        for c in const:
            if c["type"] == "colinear" and selected==c["targets"]:
                already = True
                break
        if not already:
            add_button("colinear")

    if l_count==1 and p_count==0 and c_count==0:
        #sadece bir çizgi seçilmişse uzaklık yazı kutusu eklenir
        add_input_box("dis")
    else:
        #bu durum sağlanmıyorsa zaten önceden eklenmiş olabilecek yazı kutuları silinir
        new_input_boxes = []
        for i in input_boxes:
            if "dis" in input_boxes_state:
                input_boxes_state.pop("dis")
            else:
                new_input_boxes.append(i)
        input_boxes = new_input_boxes

    if l_count==2 and p_count == 1:
        #iki çizgi ve bir nokta seçilmişse ve seçilen iki çizgi seçilen noktayı paylaşıyorsa
        #radyan ve derece cinsinden girilebilen açı yazı kutuları eklenir
        lst = []
        point = None
        check = True
        for s in list(selected):
            if type(s) == tuple:
                lst.append(s)
            else:
                point = s

        for l in lst:
            if point not in set(l):
                check = False
                break
        if check:
            add_input_box("deg")
            add_input_box("rad")
    if c_count==1 and l_count==0:
        #bir daire seçilmişse daireye nokta ekle düğmesi eklenir
        add_button("circlept")
    if c_count==1 and l_count==1:
        #bir daire ve bir çizgi seçilirse daireye teğet yap düğmesi eklenir
        add_button("circletan")
    if selected_regs != []:
        #eğer seçilen bölge varsa alan yazı kutusu eklenir
        add_input_box("area")


    
    draw_input_boxes()
    #her turda yazı kutuları çizilir


    pygame.time.delay(100)

    for pname in points:
        #listedeki noktalar isimleri ile beraber ekrana çizilir
        #seçilmiş olmaları durumunda veya üzerlerine fare ile gelinmesi durumunda mavi çizilirler
        pos = pygame.mouse.get_pos()
        x,y = points[pname]
        b = ((x-pos[0])**2 + (y-pos[1])**2)**0.5 <= 8
        if pname in selected or b:
            pygame.draw.circle(win,(0,0,255),points[pname],8)
        else:
            pygame.draw.circle(win,(0,0,0),points[pname],8)
        t = font.render(pname,True,(0,0,0))
        win.blit(t, (points[pname][0]-20,points[pname][1]-20))

    for l in lines:
        #çizgiler eğer belirlenmişse uzunluklarıyla beraber çizilirler
        #seçilmiş olmaları durumunda mavi çizilirler
        for c in const:
            if c["type"] == "dis" and l in c["targets"]:
                p1,p2 = points[l[0]],points[l[1]]
                x,y = (p1[0] + p2[0])/2, (p1[1] + p2[1])/2
                t = font.render(c["value"],True,(0,0,0))
                win.blit(t, (x,y-20))
        if l in selected:
            pygame.draw.line(win,(0,0,255),points[l[0]],points[l[1]],width=5)
        else:
            pygame.draw.line(win,(0,0,0),points[l[0]],points[l[1]],width=5)

    for c in circles:
        #daireler seçilmiş olmaları durumunda mavi olacak şekilde ekrana çizilirler
        dis_pt = list(set(c[1]) - set([c[0]]))[0]
        x1,y1 = points[dis_pt]
        x0,y0 = points[c[0]]
        dis = ((x1-x0)**2 + (y1-y0)**2)**0.5
        if c in selected_c:
            pygame.draw.circle(win,(0,0,255),points[c[0]],dis,width=5)
        else:
            pygame.draw.circle(win,(0,0,0),points[c[0]],dis,width=5)
            
    for event in pygame.event.get():
        #kullanıcı girdilerinin yorumlandığı döngü
        if event.type == pygame.QUIT:
            #kullanıcı programı kapaması durumunda döngü durdurulur ve kullanıcının durdurduğu "forced" değişkenine kaydedilir
            run = False
            forced = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                #kullanıcı F1 e basması durumunda çizimi sonlandırmış olur
                lines_rel = []

                for l in lines:
                    lines_rel.append({"line":l,"line_vals":(points[l[0]],points[l[1]])})
                    for pname in points:
                        if pname not in set(lines_rel[-1]["line"]):
                            colinear = False
                            for c in const:
                                if c["type"] == "colinear" and c["targets"] == set([l[0],l[1],pname]):
                                    colinear = True
                                    break
                            if not colinear:
                                lines_rel[-1][pname] = line_pt_rel(lines_rel[-1]["line_vals"],points[pname])
                    lines_rel[-1].pop("line_vals")
                #önce noktaların çizgilerin sağ veya solunda olduğu lines_rel listesine kaydedilir

                print(lines_rel)
                lines_dict = {}
                circles_dict = {}
                p=Plane()
                points_dict = {}
                for pt in points:
                    points_dict[pt] = p.add_point()
                #düzlem oluşturulur ve noktalar düzleme eklenir

                for l in lines:
                    lines_dict[l] = p.add_line(points_dict[l[0]],points_dict[l[1]])
                #çizgiler düzleme yerleştirilir

                for c in circles:
                    center,line = c[0],c[1]
                    radius = p.line_length(lines_dict[line])
                    circles_dict[c] = p.add_circle(points_dict[center],radius)
                #daireler düzleme yerleştirilir

                for c in const:
                    if c["type"] in set(["deg","dis","rad","area"]):
                        expr = sym.sympify(c["value"],convert_xor=True)
                        for var in list(expr.free_symbols):
                            if var not in p.varlst:
                                p.add_custom_sym(var)
                        c["value"] = expr
                #değer girilen kısıtlamalarda kullanıcının tanımladığı değişkenler olup olmadığı kontrol edilir,
                #eğer varsa düzleme eklenir
                       
                for rel in lines_rel:
                    l = lines_dict[rel["line"]]
                    for pt in rel:
                        if pt != "line":
                            point = points_dict[pt]
                            print(l,point,rel[pt])
                            p.line_point_rel(l,point,rel[pt])

                #lines_rel'in öğeleri eşitsizlik olarak kaydedilir
                


                for c in const:
                    #farklı kısıtlama tiplerine göre farklı eşitlikler hata fonksiyonuna eklenir
                    if c["type"] == "parallel":
                        #paralellik durumu
                        ls = list(c["targets"])
                        p.paral_lines(lines_dict[ls[0]], lines_dict[ls[1]])
                    elif c["type"] == "perp":
                        #diklik durumu
                        ls = list(c["targets"])
                        p.perp_lines(lines_dict[ls[0]], lines_dict[ls[1]])
                    elif c["type"] == "eqdis":
                        #eş uzunluk durumu
                        ls = list(c["targets"])
                        p.eq_distance(lines_dict[ls[0]], lines_dict[ls[1]])
                    elif c["type"] == "colinear":
                        #doğrusallık durumu
                        ls = list(c["targets"])
                        p.colinear_3pts(points_dict[ls[0]],points_dict[ls[1]],points_dict[ls[2]])
                    elif c["type"] == "dis":
                        #uzunluk durumu
                        ls = list(c["targets"])[0]
                        p.distance_2pts(points_dict[ls[0]],points_dict[ls[1]],c["value"])
                    elif c["type"] == "deg":
                        #derece cinsinden açı durumu
                        ls = list(c["targets"])
                        lin = []
                        pt = None
                        for i in ls:
                            if type(i) == tuple:
                                lin.append(lines_dict[i])
                            else:
                                pt = points_dict[i]

                        p.angle(lin[0],lin[1],pt,degtorad(c["value"]))

                    elif c["type"] == "rad":
                        #radyan cinsinden açı durumu
                        ls = list(c["targets"])
                        lin = []
                        pt = None
                        for i in ls:
                            if type(i) == tuple:
                                lin.append(lines_dict[i])
                            else:
                                pt = points_dict[i]

                        p.angle(lin[0],lin[1],pt,c["value"])
                    elif c["type"] == "area":
                        #seçilen bölgelerin alanı durumu
                        regions = []
                        for poly in c["targets"]:
                            varli = []
                            for pname in poly["pnames"]:
                                varli.append(points_dict[pname])
                            regions.append(varli)
                        p.area_of_regions(regions,c["value"])

                    elif c["type"] == "circlept":
                        #daire üzerinde nokta durumu
                        pt,circle = None,None
                        for i in c["targets"]:
                            if type(i) == tuple:
                                circle = circles_dict[i]
                            else:
                                pt = points_dict[i]
                        p.point_on_circle(circle,pt)

                    elif c["type"] == "circletan":
                        #daireye teğet çizgi durumu
                        line,circle = None,None
                        for i in c["targets"]:
                            if type(i[1]) == tuple:
                                circle = circles_dict[i]
                            else:
                                line = lines_dict[i]
                        p.line_tangent_circle(circle,line)

                print(p.cost)
                p.solve()
                p.plot()
                #sorun çözülür ve grafiği çizilir

                answers = p.table
                #cevaplar kullanıcının soru ifadesini sorgulaması üzere kaydedilir

                for c in const:
                    if "value" in c:
                        c["value"] = str(c["value"])

            if event.key == pygame.K_ESCAPE:
                #ESC'ye basılması durumunda bütün seçimler kaldırılır
                selected = set()
                selected_regs = []
                selected_c = {}

            else:
                #farklı bir tuşa basılması durumunda eğer o sırada aktif bir yazı kutusu varsa yazı ona yazılır
                for box in input_boxes:
                    state = input_boxes_state[box]
                    if state["active"]:
                        if event.key == pygame.K_BACKSPACE:
                            input_boxes_state[box]["text"] = state["text"][:-2] + "|"
                        elif event.key == pygame.K_RETURN:
                            state["text"] = state["text"][:-1]
                            if box == "area":
                                const.append({"type":box, "targets":selected_regs, "value": state["text"]})
                            else:
                                const.append({"type":box, "targets":selected, "value": state["text"]})
                            s = list(selected)
                            if box=="dis":
                                add_log(s[0][0] + s[0][1] + " çizgisinin uzunluğu " + state["text"])
                            elif box=="rad" or box=="deg":
                                pt = None
                                ls = []
                                for i in s:
                                    if type(i) == tuple:
                                        ls.append(i)
                                    else:
                                        pt = i
                                nlst = []
                                for i in ls:
                                    nlst.append(list(set(i) - set(pt))[0])
                                add_log(nlst[0] + pt + nlst[1] + " açısı " + state["text"])
                            elif box=="query":
                                forced=False
                                run = False
                            elif box=="area":
                                add_log("seçilen alanlar toplamı " + state["text"])
                            selected = set()
                            selected_regs = []
                        else:
                            input_boxes_state[box]["text"] = state["text"][:-1] + event.unicode + "|"
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            if event.button == 3:
                #sağ tıklama durumunda bölge seçimi aktif hale gelir
                for poly in regpts:
                    if pt_in(pos,poly["pts"]):
                        already = False
                        for r in selected_regs:
                            if r["pnames"] == poly["pnames"]:
                                already = True
                                break
                        if not already:
                            selected_regs.append(poly)
                            break
                #farenin kordinatlarını içine alan en küçük bölge zaten seçilmemişse seçilenler içine kaydedilir
            else:
                #sol tıklama durumu
                if drawingrect.collidepoint(pos):
                    #eğer farenin kordinatları çizim penceresinin içine geliyorsa
                    found = False
                    for pname in points:
                        px,py = points[pname][0],points[pname][1]
                        mx,my = pos[0],pos[1]
                        dis = ((px-mx)**2 + (py-my)**2)**0.5
                        if dis <= 8:
                            selected.add(pname)
                            found = True
                            break
                    #seçilmiş nokta olup olmadığına bakılır
                    if found:
                        print(points)
                        continue

                    for l in list(lines):
                        lcords = (points[l[0]],points[l[1]])
                        if point_inline(lcords,pos):
                            selected.add(l)
                            found = True
                    #sonra seçilmiş çizgi olup olmadığına bakılır

                    if found:
                        continue

                    for c in circles:
                        pt,line=c[0],c[1]
                        dist_pt = list(set(line) - set([pt]))[0]
                        x1,y1 = points[dist_pt]
                        x,y = points[pt]
                        circle_dist = ((x1-x)**2 + (y1-y)**2)**0.5
                        mouse_dist = ((x-pos[0])**2 + (y-pos[1])**2)**0.5
                        if abs(mouse_dist-circle_dist) < 6:
                            selected_c[c] = pos
                            found=True
                            break
                    if found:
                        continue
                    #ardından seçilmiş daire olup olmadığına bakılır

                    #bu işlemler sırasında seçilen bir şey bulunursa seçilmiş olarak eklenir

                if drawingrect.collidepoint(pos):
                    #seçilen birşey yok ise yeni bir nokta oluşturulur
                    points[pt_chars[0]],pt_chars = pygame.mouse.get_pos(),pt_chars[1:]

                elif optionrect.collidepoint(pos):
                    #eğer farenin kordinatları seçenek penceresinin içine geliyorsa
                    for btn in buttons:
                        if btn[0].collidepoint(pos):
                            #basılan düğme olup olmadığı kontrol edilir

                            if btn[1] == "del":
                                #eğer silme düğmesine basılırsa
                                #seçilen noktaları ve çizgileri siler, seçilen noktaları içeren çizgileri de siler

                                newconst = []
                                for c in const:
                                    tset = set()
                                    for t in c["targets"]:
                                        if type(t) == tuple:
                                            tset.add(t[0])
                                            tset.add(t[1])
                                        tset.add(t)

                                    if len(tset.intersection(selected)) == 0:
                                        newconst.append(c)
                                const = newconst
                                txt_lst = []
                                for s in list(selected):
                                    if type(s) is tuple:
                                        txt_lst.append(s[0] + s[1])
                                        try:
                                            lines.remove(s)
                                        except:
                                            pass
                                    else:
                                        txt_lst.append(s)
                                        points.pop(s)
                                        pt_chars = s + pt_chars
                                        rem = set()
                                        for l in lines:
                                            if l[0] == s or l[1]==s:
                                                txt_lst.append(l[0] + l[1])
                                                rem.add(l)
                                        lines = lines - rem
                                add_log(", ".join(txt_lst) + " silindi")
                                selected = set()
                                        

                            elif btn[1] == "line":
                                #iki nokta arasında bir çizgi oluşturur
                                l = tuple(list(selected))
                                lines.add(l)
                                add_log(l[0] + l[1] + " eklendi")
                                print(lines)

                                selected = set()

                            elif btn[1] == "parallel":
                                #iki çizgi arasında paralellik olduğunu kısıtlama listesine ekler
                                s = tuple(list(selected))
                                l1 = s[0]
                                l2 = s[1]
                                const.append({"type":"parallel", "targets":selected})
                                add_log(l1[0] + l1[1] + " ve " + l2[0] + l2[1] + " paralel")

                                selected = set()

                            elif btn[1] == "perp":
                                #iki çizgi arasında diklik olduğunu kısıtlama listesine ekler
                                s = tuple(list(selected))
                                l1 = s[0]
                                l2 = s[1]
                                const.append({"type":"perp", "targets":selected})
                                add_log(l1[0] + l1[1] + " ve " + l2[0] + l2[1] + " dik")

                                selected = set()

                            elif btn[1] == "eqdis":
                                #iki çizgi arasında eşlik olduğunu kısıtlama listesine ekler
                                s = tuple(list(selected))
                                l1 = s[0]
                                l2 = s[1]
                                const.append({"type":"eqdis", "targets":selected})
                                add_log(l1[0] + l1[1] + " ve " + l2[0] + l2[1] + " eş uzunlukta")

                                selected = set()

                            elif btn[1] == "colinear":
                                #üç nokta arasında doğrusallık olduğunu kısıtlama listesine ekler
                                s = tuple(list(selected))
                                p1 = s[0]
                                p2 = s[1]
                                p3 = s[2]
                                const.append({"type":"colinear", "targets":selected})
                                add_log(p1 + ", " + p2 + " ve " + p3 + " doğrusal")
                                selected = set()
                            elif btn[1] == "circle":
                                #seçilmiş nokta merkez, çizgi yarıçap olacak şekilde bir daire oluşturur
                                pt = None
                                line = None
                                for s in list(selected):
                                    if type(s) == tuple:
                                        line = s
                                    elif type(s) == str:
                                        pt = s
                                circles.add((pt,line))
                                selected = set()
                            elif btn[1] == "circlept":
                                #seçilmiş dairenin seçildiği yere nokta ekler ve o noktanın daire üzerinde olduğunu kısıtlamalara kaydeder
                                pt = None
                                for c in selected_c:
                                    pt = selected_c[c]
                                pname = pt_chars[0]
                                points[pname],pt_chars = pt,pt_chars[1:]
                                const.append({"type":"circlept","targets":set([pname]).union(set(selected_c))})
                                selected_c = {}

                            elif btn[1] == "circletan":
                                #seçilen çizginin seçilen daireye teğet olduğunu kısıtlamalara ekler
                                const.append({"type":"circletan","targets":selected.union(set(selected_c))})
                                selected = set()
                                selected_c = {}
                            print(const)



                    for fun in input_boxes:
                        state = input_boxes_state[fun]
                        if state["rect"].collidepoint(pos):
                            #aktif olmayan bir yazı kutusuna tıklanması durumunda o yazı kutusu aktif hale gelir
                            #ve diğer yazı kutuları aktifliklerini kaybederler
                            if state["active"] == False:
                                state["active"] = True
                                state["text"] = "|"
                        else:
                            state["active"] = False
                            
    pygame.display.update()

            
if not forced:
    #ana döngü kullanıcı zorlaması olmadan bitirildiği durumda kullanıcının istediği soru ifadesi cevaplanır
    value = None
    for c in const:
        if c["type"] == "query":
            value = c["value"]
    expr = sym.sympify(value,convert_xor=True)
    varvals = [(i,answers[i]) for i in answers]
    print(expr)
    print(varvals)
    answer = float(expr.subs(varvals))
    linlist = subprocess.run(["./ries","-c",str(answer),"-s"], capture_output=True,text=True).stdout
    #ifadenin olası kapalı hali ries e tahmin ettirilir
    linlist = linlist[linlist.find("ries")+4:]
    linlist = linlist[:linlist.find("(for more")]
    linlist = linlist.split("\n")
    linlist = [st.strip() for st in linlist]
    linlist = [st for st in linlist if st != ""]
    linlist = [st[:st.find("for")] for st in linlist]
    linlist = [st.strip() for st in linlist]
    linlist = [st[4:] for st in linlist]
    beg = [f"Cevap:{answer}",f"Yuvarlanmış:{round(answer,2)}","RIES Tahminleri:"]
    linlist = beg + linlist
    while True:

        win.fill((255,255,255))
        x,y = 20,100
        for i in linlist:
            t = font.render(i,True,(0,0,0))
            win.blit(t,(x,y))
            y+=20
        pygame.display.update()
pygame.quit()
