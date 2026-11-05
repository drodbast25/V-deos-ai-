import sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1920,1080; FPS=30; DUR=63.5
FD='/usr/share/fonts/opentype/inter/'
_fc={}
def F(w,s):
    k=(w,s)
    if k not in _fc: _fc[k]=ImageFont.truetype(FD+{'b':'Inter-Bold.otf','xb':'Inter-ExtraBold.otf','sb':'Inter-SemiBold.otf','m':'Inter-Medium.otf','l':'Inter-Light.otf'}[w],s)
    return _fc[k]
COPPER=(242,148,82); WHITE=(255,255,255); DARK=(12,16,22)
def clamp(x): return max(0.0,min(1.0,x))
def eo(x): x=clamp(x); return 1-(1-x)**3
def ei(x): x=clamp(x); return x**3
def win(t,a,b,fi=0.6,fo=0.5):
    """visibility in/out progress"""
    return eo((t-a)/fi), ei((t-(b-fo))/fo)
def text(d,xy,s,font,fill,alpha=1.0,anchor='la',spacing=0):
    if alpha<=0: return
    c=fill+(int(255*clamp(alpha)),)
    sh=(0,0,0,int(110*clamp(alpha)))
    if spacing:
        x,y=xy
        for ch in s:
            d.text((x+2,y+2),ch,font=font,fill=sh,anchor=anchor); x+=font.getlength(ch)+spacing
    else: d.text((xy[0]+2,xy[1]+2),s,font=font,fill=sh,anchor=anchor)
    if spacing:
        x,y=xy
        for ch in s:
            d.text((x,y),ch,font=font,fill=c,anchor=anchor); x+=font.getlength(ch)+spacing
    else: d.text(xy,s,font=font,fill=c,anchor=anchor)
def tw(s,font,spacing=0): return font.getlength(s)+spacing*len(s)

# pre-baked gradients
def vgrad(h,top,bot):
    g=Image.new('L',(1,h))
    for y in range(h): g.putpixel((0,y),int(top+(bot-top)*y/(h-1)))
    return g
BOT=Image.new('RGBA',(W,H),(0,0,0,0)); BOT.putalpha(vgrad(H,0,0).resize((W,H)))
bg=vgrad(520,0,215).resize((W,520)); BOTG=Image.new('RGBA',(W,520),DARK+(0,)); BOTG.putalpha(bg)
lg=Image.new('L',(1300,1)); [lg.putpixel((x,0),int(200*(1-x/1299)**1.6)) for x in range(1300)]
LEFTG=Image.new('RGBA',(1300,H),DARK+(0,)); LEFTG.putalpha(lg.resize((1300,H)))
VIG=Image.new('L',(W,H),0); dv=ImageDraw.Draw(VIG); dv.ellipse((-300,-250,W+300,H+250),fill=255); VIG=VIG.filter(ImageFilter.GaussianBlur(180))
VIGL=VIG.point(lambda v:int((255-v)*0.55)); VIGI=Image.new('RGBA',(W,H),(0,0,0,0)); VIGI.putalpha(VIGL)

def layer_alpha(img,a):
    if a>=1: return img
    r,g,b,al=img.split(); al=al.point(lambda v:int(v*a)); return Image.merge('RGBA',(r,g,b,al))

def chapter(fr,t,a,b,num,title,sub):
    pin,pout=win(t,a,b,0.7,0.6); vis=pin*(1-pout)
    if vis<=0: return
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    # dark wash
    d.rectangle((0,0,W,H),fill=DARK+(int(110*vis),))
    cx,cy=W//2,H//2
    # number
    text(d,(cx,cy-120+30*(1-pin)),num,F('sb',30),COPPER,vis,'mm')
    # lines expanding
    lw=int(260*eo((t-a-0.1)/0.8))*(1-pout)
    d.rectangle((cx-40-lw,cy-122,cx-40,cy-119),fill=COPPER+(int(255*vis),))
    d.rectangle((cx+40,cy-122,cx+40+lw,cy-119),fill=COPPER+(int(255*vis),))
    # title reveal per-letter
    f=F('xb',96); total=tw(title,f,6); x=cx-total/2
    for i,ch in enumerate(title):
        p=eo((t-a-0.15-i*0.035)/0.5)
        text(d,(x,cy-10+40*(1-p)),ch,f,WHITE,p*(1-pout),'ls')
        x+=f.getlength(ch)+6
    text(d,(cx,cy+60+20*(1-eo((t-a-0.5)/0.6))),sub,F('l',36),WHITE,eo((t-a-0.5)/0.6)*(1-pout)*0.92,'mm')
    fr.alpha_composite(L)

def card(fr,t,a,b,kicker,title,lines,x=110,y=None,width=None):
    pin,pout=win(t,a,b,0.7,0.5)
    if pin<=0 or pout>=1: return
    ft=F('xb',62); fl=F('m',34); fk=F('sb',24)
    tws=[tw(title,ft)]+[tw(l,fl) for l in lines]
    w=int(max(tws)+40) if width is None else width
    hgt=50+80+len(lines)*50
    if y is None: y=H-110-hgt
    L=Image.new('RGBA',(W,H),(0,0,0,0))
    L.alpha_composite(BOTG,(0,H-520))
    d=ImageDraw.Draw(L)
    off=-60*(1-pin)+(-40*pout)
    vis=(1-pout)
    # accent bar grows
    bh=int(hgt*eo((t-a)/0.6))
    d.rectangle((x-30,y,x-24,y+bh),fill=COPPER+(int(255*vis),))
    text(d,(x+off,y),kicker.upper(),fk,COPPER,eo((t-a-0.1)/0.5)*vis,spacing=5)
    # title with mask wipe
    p=eo((t-a-0.15)/0.6)
    text(d,(x+off*0.6,y+38+20*(1-p)),title,ft,WHITE,p*vis)
    for i,l in enumerate(lines):
        p=eo((t-a-0.35-i*0.18)/0.6)
        text(d,(x+off*0.3,y+128+i*50+15*(1-p)),l,fl,WHITE,p*vis*0.92)
    fr.alpha_composite(layer_alpha(L,1))

def tag(fr,t,a,b,s,x=110,y=90,icon=True):
    pin,pout=win(t,a,b,0.5,0.4); vis=pin*(1-pout)
    if vis<=0: return
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    f=F('sb',26); w=tw(s,f,3)+ (70 if icon else 44)
    ww=int(w*eo((t-a)/0.5))
    d.rounded_rectangle((x,y,x+ww,y+58),radius=29,fill=DARK+(int(170*vis),))
    if icon:
        cx,cy=x+32,y+29
        d.ellipse((cx-9,cy-9,cx+9,cy+9),fill=COPPER+(int(255*vis),))
        d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=DARK+(int(255*vis),))
    text(d,(x+(56 if icon else 22),y+29),s.upper(),f,WHITE,eo((t-a-0.2)/0.4)*(1-pout),'lm',spacing=3)
    fr.alpha_composite(L)

STEPS=['Perforación','Tronadura','Carguío','Transporte','Procesamiento']
def process(fr,t,a,b,active=2):
    pin,pout=win(t,a,b,0.8,0.6); vis=pin*(1-pout)
    if vis<=0: return
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(BOTG,(0,H-520)); d=ImageDraw.Draw(L)
    x0,x1,y=160,W-160,H-150
    text(d,(x0,y-190),'DE LA ROCA AL COBRE',F('sb',24),COPPER,eo((t-a)/0.5)*(1-pout),spacing=5)
    text(d,(x0,y-150),'Así se mueve el mineral en el rajo',F('xb',56),WHITE,eo((t-a-0.15)/0.6)*(1-pout))
    n=len(STEPS); step=(x1-x0)/(n-1)
    prog=eo((t-a-0.5)/4.0)
    d.rectangle((x0,y-2,x1,y+2),fill=(255,255,255,int(70*vis)))
    d.rectangle((x0,y-2,x0+(x1-x0)*prog,y+2),fill=COPPER+(int(255*vis),))
    for i,s in enumerate(STEPS):
        cx=x0+i*step; reached=prog*(n-1)>=i-0.001
        p=eo((t-a-0.5-i*1.0)/0.5)
        r=14 if i!=active else 14+4*math.sin((t-a)*3)**2+4
        if reached:
            d.ellipse((cx-r,y-r,cx+r,y+r),fill=COPPER+(int(255*vis),))
            if i==active:
                rr=r+12+6*((t*1.2)%1); d.ellipse((cx-rr,y-rr,cx+rr,y+rr),outline=COPPER+(int(200*vis*(1-((t*1.2)%1))),),width=3)
        else:
            d.ellipse((cx-10,y-10,cx+10,y+10),outline=(255,255,255,int(160*vis)),width=3)
        col=WHITE if reached else (200,200,200)
        text(d,(cx,y+48+12*(1-p)),s,F('b' if i==active else 'm',32 if i==active else 28),col,max(0.45,p)*vis if reached else 0.45*vis,'mt')
        text(d,(cx,y-40),f'0{i+1}',F('sb',22),COPPER if reached else (200,200,200),vis*(1 if reached else 0.5),'mb')
    fr.alpha_composite(L)

def chips(fr,t,a,b,kicker,title,items):
    pin,pout=win(t,a,b,0.7,0.5); vis=pin*(1-pout)
    if vis<=0: return
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(BOTG,(0,H-520)); d=ImageDraw.Draw(L)
    x,y=110,H-330
    d.rectangle((x-30,y,x-24,y+int(220*eo((t-a)/0.6))),fill=COPPER+(int(255*vis),))
    text(d,(x,y),kicker.upper(),F('sb',24),COPPER,vis,spacing=5)
    text(d,(x,y+38),title,F('xb',62),WHITE,eo((t-a-0.15)/0.6)*(1-pout))
    cx=x; f=F('sb',30)
    for i,s in enumerate(items):
        p=eo((t-a-0.5-i*0.25)/0.5)
        w=tw(s,f)+56
        yy=y+150+20*(1-p)
        d.rounded_rectangle((cx,yy,cx+w,yy+64),radius=32,fill=(255,255,255,int(235*p*(1-pout))))
        text(d,(cx+28,yy+32),s,f,DARK,p*(1-pout),'lm')
        cx+=w+18
    fr.alpha_composite(L)

def intro(fr,t):
    a,b=0.3,4.4
    pin,pout=win(t,a,b,0.9,0.6)
    if pin<=0 or pout>=1: return
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(LEFTG,(0,0)); 
    L=layer_alpha(L,pin*(1-pout)); d=ImageDraw.Draw(L)
    x,y=130,330
    vis=1-pout
    lw=int(120*eo((t-a)/0.7)); d.rectangle((x,y,x+lw,y+5),fill=COPPER+(int(255*vis),))
    text(d,(x,y+30),'VISITA A FAENA',F('sb',28),COPPER,eo((t-a-0.1)/0.5)*vis,spacing=6)
    f=F('xb',128)
    for li,word in enumerate(['MANTOS','BLANCOS']):
        xx=x
        for i,ch in enumerate(word):
            p=eo((t-a-0.25-li*0.2-i*0.04)/0.55)
            text(d,(xx,y+90+li*125+50*(1-p)),ch,f,WHITE,p*vis)
            xx+=f.getlength(ch)+4
    p=eo((t-a-0.9)/0.6)
    text(d,(x,y+370+15*(1-p)),'Embajadora de Nueva Zelanda en Chile',F('m',40),WHITE,p*vis)
    p=eo((t-a-1.15)/0.6)
    text(d,(x,y+430+15*(1-p)),'Región de Antofagasta · Desierto de Atacama',F('l',30),(230,230,230),p*vis)
    fr.alpha_composite(L)

def outro(fr,t):
    a=58.6
    if t<a: return
    p=eo((t-a)/1.0)
    L=Image.new('RGBA',(W,H),DARK+(int(200*p),)); d=ImageDraw.Draw(L)
    cx,cy=W//2,H//2
    fo=clamp((t-(DUR-1.0))/1.0)
    v=1-fo
    p1=eo((t-a-0.4)/0.8)
    f=F('xb',84)
    s1,s2,s3='NUEVA ZELANDA','×','CHILE'
    w1,w2,w3=tw(s1,f),tw(s2,f),tw(s3,f); gap=40; tot=w1+w2+w3+2*gap
    x=cx-tot/2
    text(d,(x-60*(1-p1),cy-40),s1,f,WHITE,p1*v,'ls')
    text(d,(x+w1+gap,cy-40),s2,f,COPPER,eo((t-a-0.7)/0.6)*v,'ls')
    text(d,(x+w1+w2+2*gap+60*(1-p1),cy-40),s3,f,WHITE,p1*v,'ls')
    lw=int(300*eo((t-a-0.9)/0.8)); d.rectangle((cx-lw,cy+5,cx+lw,cy+9),fill=COPPER+(int(255*v),))
    p2=eo((t-a-1.2)/0.8)
    text(d,(cx,cy+70+15*(1-p2)),'Socios para la minería del futuro',F('l',44),WHITE,p2*v,'mm')
    p3=eo((t-a-1.7)/0.8)
    text(d,(cx,cy+140),'MANTOS BLANCOS · ANTOFAGASTA, CHILE',F('sb',24),COPPER,p3*v*0.9,'mm')
    fr.alpha_composite(L)

def frame(t):
    fr=Image.new('RGBA',(W,H),(0,0,0,0))
    fr.alpha_composite(VIGI)
    intro(fr,t)
    tag(fr,t,4.3,8.7,'Briefing con el equipo de la faena')
    card(fr,t,4.6,8.7,'Una historia en el desierto','Más de 60 años de cobre',['Una de las faenas con más trayectoria','de la Región de Antofagasta'])
    card(fr,t,8.9,11.25,'Nueva Zelanda × Chile','Una alianza que suma',['Minería, innovación y tecnología'])
    tag(fr,t,11.35,12.4,'Equipo Mantos Blancos & Embajada de NZ',y=H-150)
    chapter(fr,t,12.6,17.4,'01','CÓMO FUNCIONA','Recorrido por el rajo y las operaciones')
    tag(fr,t,17.6,19.4,'Perforación en el rajo')
    card(fr,t,19.5,25.8,'Mina a rajo abierto','100% cobre',['Yacimiento de cobre tipo "manto"','Producción de cátodos y concentrado de cobre'])
    process(fr,t,26.2,39.7,active=2)
    tag(fr,t,39.9,42.3,'Conversación en el mirador del rajo')
    chapter(fr,t,40.2,44.3,'02','PLANES Y DESAFÍOS','La mirada hacia el futuro de la faena')
    card(fr,t,44.6,49.4,'Proyecto Fase II','Más capacidad de planta',['Concentradora hacia ~27.000 t/día','Permiso ambiental ingresado en 2026'])
    chips(fr,t,49.6,53.35,'Desafíos','Lo que viene',['Agua y energía','Productividad','Tecnología','Sostenibilidad'])
    tag(fr,t,53.5,55.0,'Sala de control')
    card(fr,t,55.1,58.6,'Planta concentradora','Espacio para innovar',['Oportunidades para tecnología','neozelandesa en la minería chilena'])
    outro(fr,t)
    return fr

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='preview':
        for ts in map(float,sys.argv[2:]):
            frame(ts).save(f'prev_{ts:05.1f}.png')
    else:
        out=sys.stdout.buffer
        for i in range(int(DUR*FPS)):
            out.write(frame(i/FPS).tobytes())
