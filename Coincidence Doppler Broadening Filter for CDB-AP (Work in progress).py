# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 22:20:01 2026

@author: bella
"""
'''This code is still a work in progress. It has some formatting issues with the file. The Filter part is complete and works just fine. To use place input
files for both detectors in input_file_m for Mirion, and input_file_o for ORTEC. output file must be a csv.'''

import numpy as np
import time
import matplotlib.pyplot as plt

input_file_m="C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_27hr_2nd_attempt_2_9_2026.txt"
input_file_o="C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_27hr_2nd_attempt_2_9_2026_ch000.txt"
output_file="C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\merged_matched_replica_7.csv"
def checking_en(fileO, fileM):
    tic=time.time()
    print("importing files")
    ORTEC=np.loadtxt(fileO, skiprows=5)
    Mirion=np.loadtxt(fileM, skiprows=5)
    print("files imported")
    #imports the files
    chORTEC=ORTEC[:, 1]#extracts the channel columns
    chMirion=Mirion[:, 1] 
    erORTEC=ORTEC[:, 2]#extracts extras columns
    erMirion=Mirion[:, 2]
    tORTEC=ORTEC[:, 0] #extracts time columns
    tMirion=Mirion[:, 0]
    difference=[] #initializes list to hold the time differences
    Aortec=0.228561433922209 #calibration constants
    Bortec=0.0933040274897069
    Amirion=0.70217495108278
    Bmirion=0.0931955498661126
    pair=[] #list to hold the coincidnence pairs
    compindx_ORTEC=[] #list to store values to check if Mirion gets used twice (as the length of the two lists will not be the same)
    compindx_Mirion=[]
    poplist3=[]
    #poplist4=[]
    pairch=[]
   #safe=[]

#--------------------------------------------------------------------------------------
    print("starting analyzation")#print statements to figure out where bugs are
    tORTEC = [tORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
    erORTEC=[erORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
    chORTEC = [chORTEC[i] for i, v, in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]#problem need to figure out better way to do this
    chORTEC = [chORTEC[i] for i, v in enumerate(erORTEC) if v == 0] #enumerate pairs indecies with values
    tORTEC = [tORTEC[i] for i, v in enumerate(erORTEC) if v == 0] #enumerate pairs indecies with values #enumerate pairs indecies with values

#----------------------------------------------------------------
    tMirion = [tMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
    erMirion=[erMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
    chMirion = [chMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
    chMirion = [chMirion[i] for i, v in enumerate(erMirion) if v == 0] #enumerate pairs indecies with values
    tMirion = [tMirion[i] for i, v in enumerate(erMirion) if v == 0]#enumerate pairs indecies with values
  
    
    print("finding pairs")#print statements to figure out where bugs are    
    j=0
    sorting_o=zip(tORTEC, chORTEC)
    sorting_m=zip(tMirion, chMirion)
    sorting_o=np.array(sorted(sorting_o))#fixes things if time is out of order
    sorting_m=np.array(sorted(sorting_m))
    tORTEC=list(sorting_o[:, 0])
    chORTEC=list(sorting_o[:, 1])
    tMirion=list(sorting_m[:, 0])
    chMirion=list(sorting_m[:, 1])
    for i, to in enumerate(tORTEC):
        while j+1<len(tMirion) and abs(tORTEC[i]-tMirion[j])>=abs(tORTEC[i]-tMirion[j+1]):
            j+=1
        
        if i+1<len(tORTEC):
             if abs((tORTEC[i])-tMirion[j])<abs((tORTEC[i+1])-tMirion[j]) and abs((tORTEC[i])-tMirion[j])<abs((tORTEC[i-1])-tMirion[j]):
                 if ((((chMirion[j]*0.5)*Bmirion)+Amirion)+(((chORTEC[i]*0.5)*Bortec)+Aortec))<1030 and ((((chMirion[j]*0.5)*Bmirion)+Amirion)+(((chORTEC[i]*0.5)*Bortec)+Aortec))>1014:
                     if (tORTEC[i]-tMirion[j])<0 and (tORTEC[i]-tMirion[j])>-100:
                         compindx_ORTEC.append(i) #records this index to check it in the future
                         compindx_Mirion.append(j)
                         pair.append([to, tMirion[j]])
                         pairch.append([chORTEC[i], chMirion[j]])
                         difference.append(to-tMirion[j])
        else:
            if abs(tORTEC[i]-tMirion[j])<abs(tORTEC[i-1]-tMirion[j]):#add energy filter here
                compindx_ORTEC.append(i) #records this index to check it in the future
                compindx_Mirion.append(j)
                pair.append([to, tMirion[j]])
                pairch.append([chORTEC[i], chMirion[j]])
                difference.append(to-tMirion[j]) 
            break
    return pairch   



#__________________________________________________________________________________
d2=checking_en(input_file_o, input_file_m)  
d2=[[int(d2[l][0]*0.5), int(d2[l][1]*0.5)]  for l in range(len(d2))]
d2=sorted(d2)#sorting the channel pairs
counts=set()
counting=0
all_sum=0
for i in range(len(d2)):
    #print(d2[i-1])
    if d2[i-1][1]!=d2[i][1] or d2[i-1][0]!=d2[i][0]:#checks if this is a new set of numbers as they should be in groups as they are sorted. Helps check for duplicates and make things run faster
        if i!=0:
            counts.add((d2[i-1][0], d2[i-1][1], counting))
            #print(f"counts:{counting}")
            all_sum+=counting
            if i==len(d2)-1:
                counts.add((d2[i][0], d2[i][1], 1))
        counting=1
    else:
        counting+=1
counts=list(counts)
counts=sorted(counts)
print(all_sum)
with open(output_file,"w", newline="\r\n") as f:
    f.write("[Header]\n")
    f.write("CH1Range=2048\n")
    f.write("CH2Range=2048\n")
    f.write("CH1Offset=0\n")
    f.write("CH2Offset=0\n")
    f.write("meas.start,2019/09/26,08:34:16\n")
    f.write("meas.end,2019/09/26,08:34:31\n")
    f.write("meas.time(s),2764800\n")
    f.write("elapsed time(s),14\n")
    f.write(f"total counts,{len(d2)}\n")
    f.write("\n")
    f.write("[Data]\n")
    f.write("CH1(ch),CH2(ch),Counts\n")
    for a in range(len(counts)):
        f.write(f"{int(counts[a][0])}, {int(counts[a][1])}, {counts[a][2]}\n")
print("finished")

#missing one count somewhere but otherwise all are accounted for