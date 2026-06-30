# -*- coding: utf-8 -*-
"""
Created on Tue May 12 15:22:56 2026

@author: bella
"""

"""This code filters list mode data taken from MC2 where the ORTEC file is listed first and the Mirion file is listed second.
If calibration is changed, Aortec, Bortec, Amirion, and Bmirion have to be changed accordingly. Filtering is accomplished by removing the 
last channel, and every channel that is not the 511kev peak. Then everything in the extra's column is removed if it does not have a 0. Next everything is sorted by time,
 and matched to the closest time stamp keeping other possible matches in consideration. A file is then recorded as  a Pappy compatible file"""
import numpy as np
import time
import matplotlib.pyplot as plt
import csv
from datetime import datetime
def checking_en(fileO, fileM):
    print("importing files")
    ORTEC=np.loadtxt(fileO, skiprows=5)#skips header and loads files
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
    pairch=[]



#--------------------------------------------------------------------------------------
    print("starting analyzation")#print statements to keep track of progress
    tORTEC = [tORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]#filters out all data points not in the 511kev peak
    erORTEC=[erORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
    chORTEC = [chORTEC[i] for i, v, in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
    chORTEC = [chORTEC[i] for i, v in enumerate(erORTEC) if v == 0] #gets rid of all flagged data points
    tORTEC = [tORTEC[i] for i, v in enumerate(erORTEC) if v == 0] 

#----------------------------------------------------------------
    tMirion = [tMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]#filters out all data points not in the 511kev peak
    erMirion=[erMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
    chMirion = [chMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
    chMirion = [chMirion[i] for i, v in enumerate(erMirion) if v == 0] #gets rid of all flagged data points
    tMirion = [tMirion[i] for i, v in enumerate(erMirion) if v == 0]
  
    
    print("finding pairs")#print statements to check progress   
    j=0
    sorting_o=zip(tORTEC, chORTEC)#zips the channels and the time stamps together as they are correlated
    sorting_m=zip(tMirion, chMirion)
    sorting_o=np.array(sorted(sorting_o))#fixes things if time is out of order
    sorting_m=np.array(sorted(sorting_m))

    tORTEC=list(sorting_o[:, 0])#splits time and channels again
    chORTEC=list(sorting_o[:, 1])
    tMirion=list(sorting_m[:, 0])
    chMirion=list(sorting_m[:, 1])
    for i, to in enumerate(tORTEC):
        while j+1<len(tMirion) and abs(tORTEC[i]-tMirion[j])>=abs(tORTEC[i]-tMirion[j+1]):#finds closest time difference by iterating until the difference between the current points is smaller than the next points
            j+=1

        
        if i+1<len(tORTEC):
             if abs((tORTEC[i])-tMirion[j])<abs((tORTEC[i+1])-tMirion[j]) and abs((tORTEC[i])-tMirion[j])<abs((tORTEC[i-1])-tMirion[j]):#checks if this is the best pair to prevent duplicates
                 if ((((chMirion[j]*0.5)*Bmirion)+Amirion)+(((chORTEC[i]*0.5)*Bortec)+Aortec))<1030 and ((((chMirion[j]*0.5)*Bmirion)+Amirion)+(((chORTEC[i]*0.5)*Bortec)+Aortec))>1014:#checks if they add to 1022kev
                     if (tORTEC[i]-tMirion[j])<0 and (tORTEC[i]-tMirion[j])>-100:#checks if they are in the right time threshold since there is a time delay it must be between 0 and -100 
                         compindx_ORTEC.append(i) #records this index to check it in the future
                         compindx_Mirion.append(j)
                         pair.append([to, tMirion[j]])
                         pairch.append([chORTEC[i], chMirion[j]])

        else:

            if abs(tORTEC[i]-tMirion[j])<abs(tORTEC[i-1]-tMirion[j]):#add energy filter here
                compindx_ORTEC.append(i) #records this index to check it in the future
                compindx_Mirion.append(j)
                pair.append([to, tMirion[j]])
                pairch.append([chORTEC[i], chMirion[j]])
                difference.append(to-tMirion[j]) 
            break
    
    


#__________________________________________________________________________________
    
    difference=[pair[i][0]-pair[i][1] for i in range(len(pair)-1)]
    print("graphing")
    plt.figure()
    plt.hist(difference, bins=300)
    plt.title("Time Differences From Positron Source Dataset")
    plt.xlabel("Time Difference (1e-8 s)")
    plt.ylabel("Counts")
    plt.figure()
    chMirion=np.array(chMirion)
    plt.hist(chMirion/2, bins=int(max(chMirion)-min(chMirion)))
    plt.title("Unfiltered 511KeV Peak ORTEC")
    plt.figure()
    chORTEC=np.array(chORTEC)
    plt.hist(chORTEC/2, bins=int(max(chORTEC)-min(chORTEC)))
    plt.title("Unfiltered 511KeV Peak Mirion")
    plt.xlabel("Channels")
    plt.ylabel("Counts")
    pairch=np.array(pairch)
    plt.figure()
    plt.hist(pairch[:, 0], bins=int(max(chORTEC)-min(chORTEC)))
    plt.title("Filtered 511 KeV Peak With Just Background ORTEC")
    plt.xlabel("Channels")
    plt.ylabel("Counts")
    plt.figure()
    plt.hist(pairch[:, 1], bins=int(max(chMirion)-min(chMirion)))
    plt.title("Filtered 511 KeV Peak With Just Background Mirion")
    plt.xlabel("Channels")
    plt.ylabel("Counts")
    return  pairch#returns the channel pairs
    print("writing files")
    



d2=checking_en("D:\\Coincidence Doppler Broadening Winter 2026\\Coincidence_1hr_run_Annealed_Nickel_1st_attempt_5_11_2026_ch000.txt", "D:\\Coincidence Doppler Broadening Winter 2026\\Coincidence_1hr_run_Annealed_Nickel_1st_attempt_5_11_2026_ch001.txt")
#put file names above. Ortec then Mirion
Amirion=0.70217495108278
Bmirion=0.0931955498661126
d2=sorted(d2)#sorting the channel pairs
data=set()#creates a set to prevent duplicates
for i in range(len(d2)):
    if d2[i-1][1]!=d2[i][1]:#checks if this is a new set of numbers as they should be in groups as they are sorted. Helps check for duplicates and make things run faster
        data.add(((int(d2[i][1]*0.5), int(((d2[i][1]*0.5)*Bmirion)+Amirion), d2.count(d2[i][1]))))#adds the channel pair with number of times occured as a third column
#data=sorted(data)#sorts this again (probably don't need, but should test that this still works)

OFFSET = -0.14722999930381775 #I will have to check if PAPPY ignores these. If not these may have to be fixed
SLOPE = 0.09198000282049179
QUADRATIC = 0.0

# Input/output paths

# ---- CREATE PROSPECT-STYLE CSV ----
output_file="C:\\Users\\bella\\Downloads\\Pappy_Testing_Nickel_1hr_3rd.csv"
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)

    # Header info
    writer.writerow(["Start Time", datetime.now().strftime("%a %b %d %H:%M:%S GMT-0600 %Y")])
    writer.writerow(["Energy calibration",
                     f" Offset: {OFFSET}, Slope: {SLOPE}, Quadratic: {QUADRATIC}"])
    writer.writerow(["Live Time (s)", ""])
    writer.writerow(["Real Time (s)", ""])
    writer.writerow(["Elapsed Computational", "1000000"])
    writer.writerow(["Spectrum"])
    writer.writerow(["Channel", "Energy (keV)", "Counts"])

    # Data rows
    for w in data:
        writer.writerow([w[0], w[1], w[2]])

print(f"✅ Conversion complete! Wrote {len(data)} rows to {output_file}")
    