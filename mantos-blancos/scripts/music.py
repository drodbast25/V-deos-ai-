import numpy as np, wave
from scipy.signal import butter, sosfilt, fftconvolve
SR=44100; DUR=63.5; N=int(SR*DUR)
BPM=100; BEAT=60/BPM; BAR=4*BEAT
rng=np.random.default_rng(7)
L=np.zeros(N); R=np.zeros(N)
def midi(m): return 440*2**((m-69)/12)
def lp(x,fc,o=2): return sosfilt(butter(o,fc,fs=SR,output='sos'),x)
def hp(x,fc,o=2): return sosfilt(butter(o,fc,'high',fs=SR,output='sos'),x)
def add(sig,t0,gl=1,gr=1):
    i=int(t0*SR); j=min(N,i+len(sig))
    if i>=N: return
    L[i:j]+=sig[:j-i]*gl; R[i:j]+=sig[:j-i]*gr
# chords: Am F C G (voicings)
chords=[[57,60,64,71],[53,57,60,64],[48,55,60,64],[55,59,62,67]]
roots=[45,41,36,43]
nbars=int(np.ceil(DUR/BAR))
def section_gain(t):
    # overall intensity curve
    return np.interp(t,[0,9.6,28.8,48,57.6,63.5],[0.55,0.75,0.9,1.0,0.8,0.0])
# PAD
for b in range(nbars):
    t0=b*BAR; ch=chords[b%4]; d=BAR+1.2
    n=int(d*SR); t=np.arange(n)/SR
    env=np.minimum(1,t/0.8)*np.minimum(1,np.maximum(0,(d-t)/1.2))
    sl=np.zeros(n); sr=np.zeros(n)
    for m in ch:
        f=midi(m)
        for k,det in enumerate([-0.12,0.0,0.13]):
            ph=rng.random()*2*np.pi
            saw=2*((f*(1+det/100*3)*t+ph/(2*np.pi))%1)-1
            if k==0: sl+=saw
            elif k==2: sr+=saw
            else: sl+=saw*0.5; sr+=saw*0.5
    cut=900+600*section_gain(t0)
    sl=lp(sl,cut,4)*env; sr=lp(sr,cut,4)*env
    i=int(t0*SR); j=min(N,i+n)
    if i<N: L[i:j]+=0.022*sl[:j-i]; R[i:j]+=0.022*sr[:j-i]
# ARP pluck (16ths after intro builds)
def pluck(f,d=0.45,bright=1.0):
    n=int(d*SR); t=np.arange(n)/SR
    s=np.sin(2*np.pi*f*t)+0.35*bright*np.sin(4*np.pi*f*t)+0.12*bright*np.sin(6*np.pi*f*t)
    return s*np.exp(-t*7)*np.minimum(1,t/0.003)
pat=[0,2,1,3,2,1,3,2]
for b in range(nbars):
    t0=b*BAR; ch=chords[b%4]
    if t0>59: break
    step=BEAT/2 if b<4 else BEAT/4
    nsteps=int(BAR/step)
    for s in range(nsteps):
        t=t0+s*step
        m=ch[pat[s%8]]+12
        g=0.06*section_gain(t)*(1.0 if s%2==0 else 0.7)
        pan=0.5+0.35*np.sin(s*0.9)
        add(pluck(midi(m)),t,g*(1-pan)*2*0.7,g*pan*2*0.7)
        if b>=12 and b<24 and s%4==2:
            add(pluck(midi(m+12),0.3,0.5),t,g*0.5,g*0.6)
# BASS from bar 4
for b in range(4,nbars):
    t0=b*BAR
    if t0>57.6: break
    f=midi(roots[b%4])
    for s in range(8):
        n=int(BEAT/2*SR*0.95); t=np.arange(n)/SR
        s_=np.tanh(2*np.sin(2*np.pi*f*t))*np.exp(-t*3)*np.minimum(1,t/0.005)
        s_=lp(s_,400)
        g=0.12*(1 if s%2==0 else 0.75)
        add(s_,t0+s*BEAT/2,g,g)
# KICK, SHAKER, CLAP
def kick():
    n=int(0.35*SR); t=np.arange(n)/SR
    f=45+90*np.exp(-t*30); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t*9)
def shaker():
    n=int(0.08*SR); t=np.arange(n)/SR
    return hp(rng.standard_normal(n),6000)*np.exp(-t*60)
def clap():
    n=int(0.25*SR); t=np.arange(n)/SR
    e=np.exp(-t*25)+0.6*np.exp(-np.maximum(0,t-0.012)*25)*(t>0.012)
    return lp(hp(rng.standard_normal(n),900),3500)*e
K=kick()
for b in range(4,nbars):
    for q in range(4):
        t=b*BAR+q*BEAT
        if t>57.6: break
        add(K,t,0.32,0.32)
        if b>=8:
            for e in range(2):
                add(shaker(),t+e*BEAT/2+BEAT/4,0.035,0.05)
        if b>=12 and q in(1,3):
            add(clap(),t,0.09,0.08)
# rise before 28.8 and 48 (noise swell)
for tr in [28.8,48.0]:
    d=2.4; n=int(d*SR); t=np.arange(n)/SR
    sw=hp(rng.standard_normal(n),2000)*(t/d)**2*0.05
    add(sw,tr-d,1,1)
# impact boom at 28.8 and 39.6 and outro 58.8
for ti in [28.8,58.8]:
    n=int(3*SR); t=np.arange(n)/SR
    boom=np.sin(2*np.pi*(40+30*np.exp(-t*4))*t)*np.exp(-t*1.5)*0.35
    add(boom,ti,1,1)
# final chord sustain
t0=57.6; d=DUR-t0; n=int(d*SR); t=np.arange(n)/SR
fin=sum(np.sin(2*np.pi*midi(m)*t)*0.5+np.sin(2*np.pi*midi(m)*1.003*t)*0.5 for m in [45,57,64,69,71,76])
fin*=np.minimum(1,t/0.5)*np.exp(-t*0.35)*0.05
add(fin,t0,1,1)
# reverb
ir_n=int(2.2*SR); ti=np.arange(ir_n)/SR
irL=rng.standard_normal(ir_n)*np.exp(-ti*3.2); irR=rng.standard_normal(ir_n)*np.exp(-ti*3.2)
irL=lp(irL,5000); irR=lp(irR,5000)
wetL=fftconvolve(L,irL)[:N]; wetR=fftconvolve(R,irR)[:N]
s=np.sqrt(np.sum(irL**2))
L2=L+0.35*wetL/s; R2=R+0.35*wetR/s
# master fade, normalize, soft clip
t=np.arange(N)/SR
fade=np.minimum(1,t/1.5)*np.clip((DUR-t)/3.0,0,1)
L2*=fade; R2*=fade
pk=max(np.abs(L2).max(),np.abs(R2).max())
L2=np.tanh(L2/pk*1.3)/np.tanh(1.3)*0.89; R2=np.tanh(R2/pk*1.3)/np.tanh(1.3)*0.89
out=(np.stack([L2,R2],1)*32767).astype(np.int16)
with wave.open('music.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('ok')
