#taking the input
input_file=raw_input('Enter file to be encripted with substitution cipher\n')
f=open(input_file,'r')
g=f.read()
g=g.lower() #g holds the input file in a string.


#opening the output file
output_file=raw_input('Enter file to write the output\n')
h=open(output_file,'w')


#taking the encription key as input
encription_key=raw_input("Enter encription key. Enter the letter to replace 'a'. Add a space. Then write the letter to replace 'b'...\n")




#Give input correct since there is no checking for the encription key to not have repeated alphabets.
key=encription_key.split()
if (len(key)!=26):
	print "Please enter a proper encription key with 26 alphabets"
else:	
	c={}
	m=""
	i=0
	#create a dictionary 'c' where the key is an alphabet and its value is the alphabet which replaces it
	while(i<26):
		c[chr(97+i)]=key[i]
		i=i+1
	
	#replace the key with its value from the 
	for j in range(0,len(g)):
		if g[j]>'a' and g[j]<'z':
			m=m+c[g[j]]
		else:
			m=m+g[j]

#write to the output files and close the pointers
h.write(m)
h.close()
f.close()