'''
DECRIPTING THE SUBSTITUTION CIPHER

We use the knowledge of the frequency of words. So it works only on texts of significantly large size
1. A and I are the only single letter words so you get it.
2. 'the' is by far the most commonly used word. Hence we get the letters t,h and e.
3. 'of' is the most commonly used 2 letter word.
4. continue this till we get a few common letters.
5. To find 'n' and 'd' - 'and' is the most common 3 letter word with 'a' as its first letter (we already found out what 'a' is)
6. This is the basic algorithm. There are a few backup cases for words that might not be there in the text.
'''


#input the file to be decripted
file_name=raw_input('enter file to be decripted\n')




#document must contain - the, a, of, and, which, because, for, from
A='-'
C='-'
D='-'
E='-'
F='-'
H='-'
N='-'
O='-'
T='-'
W='-'
B='-'
U='-'
S='-'
M='-'
V='-'

f=open(file_name,'r')
a=f.read()
a=a.lower()
b=len(a)
l={}
import re
# Finding A and I(if the word I exists)
I=' '
c=re.findall(r' . ',a)
k=len(c)
i=0
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123:
		if(c[i][1] in l):
			l[c[i][1]]=l[c[i][1]]+1
		else:
			l[c[i][1]]=1

high=0
for z in l:
	if l[z]>high:
		high=l[z]
		A=z
for y in l:
	if l[y]!=high:
		I=y

print ('a is'),A

#finding e separately
#for i in range(0,b):
#	c=a[i]
#	k=ord(c)
#	if(k>96 and k<123):
#		if(c in l):
#			l[c]=l[c]+1
#		else:
#			l[c]=1 
#print l
	



#FINDING T H AND E
c=re.findall(' ... ',a)
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123:
		if(c[i][1:4] in g):
			g[c[i][1:4]]=g[c[i][1:4]]+1
		else:
			g[c[i][1:4]]=1
high=0
for x in g:
	if g[x]>high:
		high=g[x]
		T=x[0]
		H=x[1]
		E=x[2]

print ("the is"),T,H,E

#FINDING N AND D(frequency of 'and' in 22.5 billion followed by 'for' which is 6.55 billion)

d=re.findall(' ... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==A:
		c=c+[d[q]]
	
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123:
		if(c[i][1:4] in g):
			g[c[i][1:4]]=g[c[i][1:4]]+1
		else:
			g[c[i][1:4]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		N=x[1]
		D=x[2]
		
print ("n and d is"),N,D



#FINDING I IF IT HASN'T BEEN FOUND BEFORE
if I==' ':
	d=re.findall(' .. ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][2]==N:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123:
			if(c[i][1:3] in g):
				g[c[i][1:3]]=g[c[i][1:3]]+1
			else:
				g[c[i][1:3]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			I=x[0]

print ('i is'),I
		

	


#FINDING O AND F(of is approx 30 billion, next is to and frequency is 19 billion,next is in and frequency is approx 17 billion)

c=re.findall(' .. ',a)
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123:
		if(c[i][1:3] in g):
			g[c[i][1:3]]=g[c[i][1:3]]+1
		else:
			g[c[i][1:3]]=1
high=0
for x in g:
	if g[x]>high and x[0]!=I and x[0]!=T:
		high=g[x]
		O=x[0]
		F=x[1]
#to checking that this word is not 'to' or 'in' by mistake
		
high2=0
if O==I or O==T:
	for x in g:
		if g[x]!=high:
			if g[x]>high2:
				high2=g[x] 
				N=x[1]
				D=x[2]

print ("o and f is"),O,F


	

#FINDING W C ('which' is 3.14 billion is highest, 'their' is 2.15 billion,'there' is 1.62 billion,'would' and 'above' also come in competition. Bt none of the other have 'i' as the 3rd letter )

d=re.findall(' ..... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][2]==H and d[q][3]==I and d[q][5]==H:
		c=c+[d[q]]
	
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123:
		if(c[i][1:6] in g):
			g[c[i][1:6]]=g[c[i][1:6]]+1
		else:
			g[c[i][1:6]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		W=x[0]
		C=x[3]

print ("w and c are"),W,C


#FINDING B U S('because' is the most common 7 letter word and we know 4 of them already)

d=re.findall(' ....... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][2]==E and d[q][3]==C and d[q][4]==A and d[q][7]==E:
		c=c+[d[q]]
	
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123 and ord(c[i][6])>96 and ord(c[i][6])<123and ord(c[i][7])>96 and ord(c[i][7])<123:
		if(c[i][1:8] in g):
			g[c[i][1:8]]=g[c[i][1:8]]+1
		else:
			g[c[i][1:8]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		B=x[0]
		U=x[4]
		S=x[5]

#if because doesn't exist
if B=='-':
	d=re.findall(' .. ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]!=H and d[q][2]==E:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123:
			if(c[i][1:3] in g):
				g[c[i][1:3]]=g[c[i][1:3]]+1
			else:
				g[c[i][1:3]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			B=x[0]
if U=='-':
	d=re.findall(' ... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==B and d[q][2]!=A and d[q][2]!=E and d[q][2]!=I and d[q][2]!=O and d[q][3]==T:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123:
			if(c[i][1:4] in g):
				g[c[i][1:4]]=g[c[i][1:4]]+1
			else:
				g[c[i][1:4]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			U=x[1]

if S=='-':
	d=re.findall(' .. ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==I and d[q][2]!=N and d[q][2]!=F and d[q][2]!=T:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123:
			if(c[i][1:3] in g):
				g[c[i][1:3]]=g[c[i][1:3]]+1
			else:
				g[c[i][1:3]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			S=x[1]
if S=='-':
	d=re.findall(' .... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==T and d[q][2]==H and d[q][3]==I:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
			if(c[i][1:5] in g):
				g[c[i][1:5]]=g[c[i][1:5]]+1
			else:
				g[c[i][1:5]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			S=x[3]
print ("b, u, s are"),B,U,S


#FINDING R (from for)


d=re.findall(' ... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==F and d[q][2]==O:
		c=c+[d[q]]
	
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123:
		if(c[i][1:4] in g):
			g[c[i][1:4]]=g[c[i][1:4]]+1
		else:
			g[c[i][1:4]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		R=x[2]
		
print ("r is"),R



#FINDING M (from 'from')

d=re.findall(' .... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==F and d[q][2]==R and d[q][3]==O:
		c=c+[d[q]]
	
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
		if(c[i][1:5] in g):
			g[c[i][1:5]]=g[c[i][1:5]]+1
		else:
			g[c[i][1:5]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		M=x[3]

#if from doesnt exist

if M=='-':
	d=re.findall(' .. ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]!=H and d[q][1]!=B and d[q][2]==E:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123:
			if(c[i][1:3] in g):
				g[c[i][1:3]]=g[c[i][1:3]]+1
			else:
				g[c[i][1:3]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			M=x[0]

if M=='-':
	d=re.findall(' .... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==S and d[q][2]==O and d[q][3]!=R and d[q][4]==E:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
			if(c[i][1:5] in g):
				g[c[i][1:5]]=g[c[i][1:5]]+1
			else:
				g[c[i][1:5]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			M=x[2]
		
print ("M is"),M


#FINDING V(from 'have')

d=re.findall(' .... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==H and d[q][2]==A and d[q][4]==E:
		c=c+[d[q]]
	
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
		if(c[i][1:5] in g):
			g[c[i][1:5]]=g[c[i][1:5]]+1
		else:
			g[c[i][1:5]]=1


high=0
for x in g:
	if g[x]>high:
		high=g[x]
		V=x[2]

#IF have doesnt exist

if V=='-':
	d=re.findall(' .... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==E and d[q][2]!=T and d[q][3]==E and d[q][4]==N:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
			if(c[i][1:5] in g):
				g[c[i][1:5]]=g[c[i][1:5]]+1
			else:
				g[c[i][1:5]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			V=x[1]
		
print ("v is"),V

























#HERE ONWARDS IT CANNOT BE GUARENTEED 
G='-'
J='-'
K='-'
L='-'
P='-'
Q='-'
X='-'
Y='-'
Z='-'

#FINDING L (first from 'all')

d=re.findall(' ... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==A and d[q][2]==d[q][3]:
		c=c+[d[q]]
	
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123:
		if(c[i][1:4] in g):
			g[c[i][1:4]]=g[c[i][1:4]]+1
		else:
			g[c[i][1:4]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		L=x[2]

#if not then in 'will'
if L=='-':
	d=re.findall(' .... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==W and d[q][2]==I and d[q][3]==d[q][4]:
			c=c+[d[q]]
	
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
			if(c[i][1:5] in g):
				g[c[i][1:5]]=g[c[i][1:5]]+1
			else:
				g[c[i][1:5]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			L=x[3]

print ("l is"),L


#FINDING Y (from by or you)

d=re.findall(' .. ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==B and d[q][2]!=A and d[q][2]!=B and d[q][2]!=C and d[q][2]!=D and d[q][2]!=E and d[q][2]!=F and d[q][2]!=H and d[q][2]!=I and d[q][2]!=M and d[q][2]!=N and d[q][2]!=R and d[q][2]!=S and d[q][2]!=T and d[q][2]!=U and d[q][2]!=W and d[q][2]!=V :
		c=c+[d[q]]
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123:
		if(c[i][1:3] in g):
			g[c[i][1:3]]=g[c[i][1:3]]+1
		else:
			g[c[i][1:3]]=1

for x in g:
	if g[x]>high:
		high=g[x]
		Y=x[1]

#if not then in 'you'
if Y=='-':
	d=re.findall(' ... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][2]==O and d[q][3]==U and d[q][1]!=A and d[q][1]!=B and d[q][1]!=C and d[q][1]!=D and d[q][1]!=E and d[q][1]!=F and d[q][1]!=H and d[q][1]!=I and d[q][1]!=M and d[q][1]!=N and d[q][1]!=R and d[q][1]!=S and d[q][1]!=T and d[q][1]!=U and d[q][1]!=W and d[q][1]!=V:
			c=c+[d[q]]

	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123:
			if(c[i][1:4] in g):
				g[c[i][1:4]]=g[c[i][1:4]]+1
			else:
				g[c[i][1:4]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			Y=x[0]

print ("y is"),Y

#FINDING P (in people and up)

d=re.findall(' ...... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][2]==E and d[q][3]==O and d[q][1]==d[q][4] and d[q][5]==L and d[q][6]==E and d[q][1]!=A and d[q][1]!=B and d[q][1]!=C and d[q][1]!=D and d[q][1]!=E and d[q][1]!=F and d[q][1]!=H and d[q][1]!=I and d[q][1]!=M and d[q][1]!=N and d[q][1]!=R and d[q][1]!=S and d[q][1]!=T and d[q][1]!=U and d[q][1]!=W and d[q][1]!=V :
		c=c+[d[q]]

k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123 and ord(c[i][6])>96 and ord(c[i][6])<123:
		if(c[i][1:7] in g):
			g[c[i][1:7]]=g[c[i][1:7]]+1
		else:
			g[c[i][1:7]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		P=x[3]

#if not then in 'up'
if P=='-':
	d=re.findall(' ... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==U and d[q][2]!=A and d[q][2]!=B and d[q][2]!=C and d[q][2]!=D and d[q][2]!=E and d[q][2]!=F and d[q][2]!=H and d[q][2]!=I and d[q][2]!=M and d[q][2]!=N and d[q][2]!=R and d[q][2]!=S and d[q][2]!=T and d[q][2]!=U and d[q][2]!=W and d[q][2]!=V:
			c=c+[d[q]]

	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123:
			if(c[i][1:3] in g):
				g[c[i][1:3]]=g[c[i][1:3]]+1
			else:
				g[c[i][1:3]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			P=x[1]
print ('p is'),P

#FINDING K

d=re.findall(' .... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][2]==N and d[q][3]==O and d[q][4]==W and d[q][1]!=A and d[q][1]!=B and d[q][1]!=C and d[q][1]!=D and d[q][1]!=E and d[q][1]!=F and d[q][1]!=H and d[q][1]!=I and d[q][1]!=M and d[q][1]!=N and d[q][1]!=R and d[q][1]!=S and d[q][1]!=T and d[q][1]!=U and d[q][1]!=W and d[q][1]!=V and d[q][1]!=P and d[q][1]!=L:
		c=c+[d[q]]

k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
		if(c[i][1:5] in g):
			g[c[i][1:5]]=g[c[i][1:5]]+1
		else:
			g[c[i][1:5]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		K=x[0]

#if not then in 'take'
if K=='-':
	d=re.findall(' .... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==T and d[q][2]==A and d[q][4]==E and d[q][3]!=A and d[q][3]!=B and d[q][3]!=C and d[q][3]!=D and d[q][3]!=E and d[q][3]!=F and d[q][3]!=H and d[q][3]!=I and d[q][3]!=M and d[q][3]!=N and d[q][3]!=R and d[q][3]!=S and d[q][3]!=T and d[q][3]!=U and d[q][3]!=W and d[q][3]!=V and d[q][3]!=P and d[q][3]!=L:
			c=c+[d[q]]

	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
			if(c[i][1:5] in g):
				g[c[i][1:5]]=g[c[i][1:5]]+1
			else:
				g[c[i][1:5]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			K=x[2]
print ('k is'),K


#FINDING G (in good)

d=re.findall(' .... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][2]==O and d[q][3]==O and d[q][4]==D and d[q][1]!=A and d[q][1]!=B and d[q][1]!=C and d[q][1]!=D and d[q][1]!=E and d[q][1]!=F and d[q][1]!=H and d[q][1]!=I and d[q][1]!=M and d[q][1]!=N and d[q][1]!=R and d[q][1]!=S and d[q][1]!=T and d[q][1]!=U and d[q][1]!=W and d[q][1]!=V and d[q][1]!=P and d[q][1]!=L :
		c=c+[d[q]]

k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
		if(c[i][1:5] in g):
			g[c[i][1:5]]=g[c[i][1:5]]+1
		else:
			g[c[i][1:5]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		G=x[0]

#if not then in 'through'
if G=='-':
	d=re.findall(' ....... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==T and d[q][2]==H and d[q][3]==R and d[q][4]==O and d[q][5]==U and d[q][7]==H and d[q][6]!=A and d[q][6]!=B and d[q][6]!=C and d[q][6]!=D and d[q][6]!=E and d[q][6]!=F and d[q][6]!=H and d[q][6]!=I and d[q][6]!=M and d[q][6]!=N and d[q][6]!=R and d[q][6]!=S and d[q][6]!=T and d[q][6]!=U and d[q][6]!=W and d[q][6]!=V and d[q][6]!=P and d[q][6]!=L:
			c=c+[d[q]]

	k=len(c)
	i=0
	g={}
	for i in range(0,k):
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123 and ord(c[i][6])>96 and ord(c[i][6])<123and ord(c[i][7])>96 and ord(c[i][7])<123:
			if(c[i][1:8] in g):
				g[c[i][1:8]]=g[c[i][1:8]]+1
			else:
				g[c[i][1:8]]=1


	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			G=x[5]
print ('g is'),G


#FINDING J (in just)

d=re.findall(' .... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][2]==U and d[q][3]==S and d[q][4]==T and d[q][1]!=A and d[q][1]!=B and d[q][1]!=C and d[q][1]!=D and d[q][1]!=E and d[q][1]!=F and d[q][1]!=H and d[q][1]!=I and d[q][1]!=M and d[q][1]!=N and d[q][1]!=R and d[q][1]!=S and d[q][1]!=T and d[q][1]!=U and d[q][1]!=W and d[q][1]!=V and d[q][1]!=G and d[q][1]!=L :
		c=c+[d[q]]

k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
		if(c[i][1:5] in g):
			g[c[i][1:5]]=g[c[i][1:5]]+1
		else:
			g[c[i][1:5]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		J=x[0]



#if not then in 'Job'
if J=='-':
	d=re.findall(' ... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][2]==O and d[q][3]==B and d[q][1]!=A and d[q][1]!=B and d[q][1]!=C and d[q][1]!=D and d[q][1]!=E and d[q][1]!=F and d[q][1]!=H and d[q][1]!=I and d[q][1]!=M and d[q][1]!=N and d[q][1]!=R and d[q][1]!=S and d[q][1]!=T and d[q][1]!=U and d[q][1]!=W and d[q][1]!=V:
			c=c+[d[q]]

	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123:
			if(c[i][1:4] in g):
				g[c[i][1:4]]=g[c[i][1:4]]+1
			else:
				g[c[i][1:4]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			J=x[0]

print ("j is"),J

#FINDING X (in next or expect)

d=re.findall(' .... ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==N and d[q][2]==E and d[q][4]==T and d[q][3]!=A and d[q][3]!=B and d[q][3]!=C and d[q][3]!=D and d[q][3]!=E and d[q][3]!=F and d[q][3]!=H and d[q][3]!=I and d[q][3]!=M and d[q][3]!=N and d[q][3]!=R and d[q][3]!=S and d[q][3]!=T and d[q][3]!=U and d[q][3]!=W and d[q][3]!=V and d[q][3]!=P and d[q][3]!=L:
			c=c+[d[q]]
		
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123:
		if(c[i][1:5] in g):
			g[c[i][1:5]]=g[c[i][1:5]]+1
		else:
			g[c[i][1:5]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		X=x[2]

#if not then in 'expect'
if X=='-':
	d=re.findall(' .... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==E and d[q][3]==P and d[q][4]==E and d[q][5]==C and d[q][6]==T and d[q][2]!=A and d[q][2]!=B and d[q][2]!=C and d[q][2]!=D and d[q][2]!=E and d[q][2]!=F and d[q][2]!=H and d[q][2]!=I and d[q][2]!=M and d[q][2]!=N and d[q][2]!=R and d[q][2]!=S and d[q][2]!=T and d[q][2]!=U and d[q][2]!=W and d[q][2]!=V:
			c=c+[d[q]]
		
	k=len(c)
	i=0
	g={}
	for i in range(0,k):
	
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123and ord(c[i][6])>96 and ord(c[i][6])<123:
			if(c[i][1:7] in g):
				g[c[i][1:7]]=g[c[i][1:7]]+1
			else:
				g[c[i][1:7]]=1

	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			X=x[1]
print ('x is'),X

#FINDING Q(IN QUESTiON AND require)

d=re.findall(' ........ ',a)
c=[]
for q in range(0,len(d)):
	if d[q][3]==E and d[q][2]==U and d[q][4]==S and d[q][5]==T and d[q][6]==I and d[q][7]==O and d[q][8]==N and d[q][1]!=A and d[q][1]!=B and d[q][1]!=C and d[q][1]!=D and d[q][1]!=E and d[q][1]!=F and d[q][1]!=H and d[q][1]!=I and d[q][1]!=M and d[q][1]!=N and d[q][1]!=R and d[q][1]!=S and d[q][1]!=T and d[q][1]!=U and d[q][1]!=W and d[q][1]!=V:
			c=c+[d[q]]
		
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123 and ord(c[i][6])>96 and ord(c[i][6])<123 and ord(c[i][7])>96 and ord(c[i][7])<123 and ord(c[i][8])>96 and ord(c[i][8])<123:
		if(c[i][1:9] in g):
			g[c[i][1:9]]=g[c[i][1:9]]+1
		else:
			g[c[i][1:9]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		Q=x[0]

#if not then in 'require'
if Q=='-':
	d=re.findall(' ....... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==R and d[q][2]==E and d[q][6]==R and d[q][4]==U and d[q][5]==I and d[q][7]==E and d[q][3]!=A and d[q][3]!=B and d[q][3]!=C and d[q][3]!=D and d[q][3]!=E and d[q][3]!=F and d[q][3]!=H and d[q][3]!=I and d[q][3]!=M and d[q][3]!=N and d[q][3]!=R and d[q][3]!=S and d[q][3]!=T and d[q][3]!=U and d[q][3]!=W and d[q][3]!=V and d[q][3]!=P and d[q][3]!=L: 
			c=c+[d[q]]

	k=len(c)
	i=0
	g={}
	for i in range(0,k):
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123 and ord(c[i][6])>96 and ord(c[i][6])<123and ord(c[i][7])>96 and ord(c[i][7])<123:
			if(c[i][1:8] in g):
				g[c[i][1:8]]=g[c[i][1:8]]+1
			else:
				g[c[i][1:8]]=1


	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			Q=x[2]
print ('q is'),Q

#FINDING Z (in organization and realize)

d=re.findall(' ............ ',a)
c=[]
for q in range(0,len(d)):
	if d[q][1]==O and d[q][2]==R and d[q][4]==A and d[q][5]==N and d[q][6]==I and d[q][3]==G and d[q][8]==A  and d[q][9]==T and d[q][10]==I and d[q][11]==O and d[q][12]==N and d[q][7]!=A and d[q][7]!=B and d[q][7]!=C and d[q][7]!=D and d[q][7]!=E and d[q][7]!=F and d[q][7]!=H and d[q][7]!=I and d[q][7]!=M and d[q][7]!=N and d[q][7]!=R and d[q][7]!=S and d[q][7]!=T and d[q][7]!=U and d[q][7]!=W and d[q][7]!=V:
		c=c+[d[q]]
		
k=len(c)
i=0
g={}
for i in range(0,k):
	
	if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123 and ord(c[i][6])>96 and ord(c[i][6])<123 and ord(c[i][7])>96 and ord(c[i][7])<123 and ord(c[i][8])>96 and ord(c[i][8])<123 and ord(c[i][9])>96 and ord(c[i][9])<123 and ord(c[i][10])>96 and ord(c[i][10])<123 and ord(c[i][11])>96 and ord(c[i][11])<123 and ord(c[i][12])>96 and ord(c[i][12])<123 :
		if(c[i][1:13] in g):
			g[c[i][1:13]]=g[c[i][1:13]]+1
		else:
			g[c[i][1:13]]=1

high=0
for x in g:
	if g[x]>high:
		high=g[x]
		Z=x[6]

#if not then in 'realize'
if Z=='-':
	d=re.findall(' ....... ',a)
	c=[]
	for q in range(0,len(d)):
		if d[q][1]==R and d[q][2]==E and d[q][3]==A and d[q][4]==L and d[q][5]==I and d[q][7]==E and d[q][6]!=A and d[q][6]!=B and d[q][6]!=C and d[q][6]!=D and d[q][6]!=E and d[q][6]!=F and d[q][6]!=H and d[q][6]!=I and d[q][6]!=M and d[q][6]!=N and d[q][6]!=R and d[q][6]!=S and d[q][6]!=T and d[q][6]!=U and d[q][6]!=W and d[q][6]!=V and d[q][6]!=P and d[q][6]!=L:
			c=c+[d[q]]

	k=len(c)
	i=0
	g={}
	for i in range(0,k):
		if ord(c[i][1])>96 and ord(c[i][1])<123 and ord(c[i][2])>96 and ord(c[i][2])<123 and ord(c[i][3])>96 and ord(c[i][3])<123 and ord(c[i][4])>96 and ord(c[i][4])<123 and ord(c[i][5])>96 and ord(c[i][5])<123 and ord(c[i][6])>96 and ord(c[i][6])<123and ord(c[i][7])>96 and ord(c[i][7])<123:
			if(c[i][1:8] in g):
				g[c[i][1:8]]=g[c[i][1:8]]+1
			else:
				g[c[i][1:8]]=1


	high=0
	for x in g:
		if g[x]>high:
			high=g[x]
			Z=x[5]
print ('z is'),Z

#
#
#
#
#
#




# REPLACING ALL THE LETTERS
z=a

for i in range(0,len(z)):
	if z[i]==A:
		z=z[:i]+'A'+z[i+1:]
	if z[i]==B:
		z=z[:i]+'B'+z[i+1:]
	if z[i]==C:
		z=z[:i]+'C'+z[i+1:]
	if z[i]==D:
		z=z[:i]+'D'+z[i+1:]
	if z[i]==E:
		z=z[:i]+'E'+z[i+1:]
	if z[i]==F:
		z=z[:i]+'F'+z[i+1:]
	if z[i]==G:
		z=z[:i]+'G'+z[i+1:]
	if z[i]==H:
		z=z[:i]+'H'+z[i+1:]
	if z[i]==J:
		z=z[:i]+'J'+z[i+1:]
	if z[i]==K:
		z=z[:i]+'K'+z[i+1:]
	if z[i]==L:
		z=z[:i]+'L'+z[i+1:]
	if z[i]==M:
		z=z[:i]+'M'+z[i+1:]
	if z[i]==N:
		z=z[:i]+'N'+z[i+1:]
	if z[i]==O:
		z=z[:i]+'O'+z[i+1:]
	if z[i]==P:
		z=z[:i]+'P'+z[i+1:]
	if z[i]==Q:
		z=z[:i]+'Q'+z[i+1:]
	if z[i]==R:
		z=z[:i]+'R'+z[i+1:]
	if z[i]==S:
		z=z[:i]+'S'+z[i+1:]
	if z[i]==T:
		z=z[:i]+'T'+z[i+1:]
	if z[i]==U:
		z=z[:i]+'U'+z[i+1:]
	if z[i]==V:
		z=z[:i]+'V'+z[i+1:]
	if z[i]==W:
		z=z[:i]+'W'+z[i+1:]
	if z[i]==X:
		z=z[:i]+'X'+z[i+1:]
	if z[i]==Y:
		z=z[:i]+'Y'+z[i+1:]
	if z[i]==Z:
		z=z[:i]+'Z'+z[i+1:]
	if z[i]==I:
		z=z[:i]+'I'+z[i+1:]
	
print z