# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 17:00:43 2026

@author: bella
"""

import numpy as np
import matplotlib.pyplot as plt
ORTEC=np.genfromtxt("C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_5thRun_3rd_Attempt_1_19_2026_ch000.txt", skip_header=5)
Mirion=np.genfromtxt("C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_5thRun_3rd_Attempt_1_19_2026_ch001.txt", skip_header=5)
#imports the files
chORTEC=list(ORTEC[:, 1])#extracts the channel columns
chMirion=list(Mirion[:, 1]) 
erORTEC=list(ORTEC[:, 2])#extracts extras columns
erMirion=list(Mirion[:, 2])
tORTEC=list(ORTEC[:, 0]) #extracts time columns
tMirion=list(Mirion[:, 0])
difference=[] #initializes list to hold the time differences
Aortec=0.228561433922209 #calibration constants
Bortec=0.0933040274897069
Amirion=0.70217495108278
Bmirion=0.0931955498661126
pair=[] #list to hold the coincidnence pairs
enORTEC=[] #list to hold the calibrated energies
enMirion=[]
compindx_ORTEC=[] #list to store values to check if Mirion gets used twice (as the length of the two lists will not be the same)
compindx_Mirion=[]
poplisto=[]
poplistm=[]#lists to pop all the necessary indicies at once to prevent changes in idicies when removing variables from a list
poplist2=[]
poplist3=[]
poplist4=[]
safe=[]
#--------------------------------------------------------------------------------------
print("starting analyzation")
for indx in range(len(erORTEC)): #extras filter 
    if abs(erORTEC[indx])>0: #checks if the extras column is not equal to 0
        poplisto.append(indx)
#-----------------------------------------------------
print("starting cleaning with extras ORTEC column")#print statements to figure out where bugs are
poplisto=sorted(poplisto, reverse=True) #inverts the poplist so that values can be popped backwards to prevent lists getting out of range and other problems
for p in poplisto: #removes the values that the extras indicated were bad
    chORTEC.pop(p)
    erORTEC.pop(p)
    tORTEC.pop(p)
#----------------------------------------------------------------
for indx in range(len(erMirion)): #extras filter 
    if abs(erMirion[indx])>0: #checks if the extras column is not equal to 0
        poplistm.append(indx)
#-------------------------------------------------------------------
print("starting cleaning with extras Mirion column")
poplistm=sorted(poplistm, reverse=True) #inverts the poplist so that values can be popped backwards to prevent lists getting out of range and other problems
for p in poplistm: #removes the values that the extras indicated were bad
    chMirion.pop(p)
    erMirion.pop(p)
    tMirion.pop(p)
#----------------------------------------------------------------------------
print("finding pairs")
for i in range(len(tORTEC)):#finds possible coincidence pairs by finding the smallest time difference
    mindifference=tORTEC[i]-tMirion[0]#sets initial time difference with first pair
    indx=0
    for j in range(len(tMirion)): 
        if abs(tORTEC[i]-tMirion[j])<abs(mindifference):#checks if magnitude of this difference is bigger or smaller
            mindifference=tORTEC[i]-tMirion[j]#if smaller, new mindifference is defined until, all possible pairs have been checked
            indx=j
    compindx_ORTEC.append(i) #records this index to check it in the future
    compindx_Mirion.append(indx)
    pair.append([tORTEC[i], tMirion[indx]])
    difference.append(mindifference)

safe=compindx_Mirion
poplist2=[i for i in range(len(chMirion))]#initializes a lit of values to pop in chMirion
safe=set(safe)#safe list needs to be put in order with no duplicates
safe=list(safe)
safe=sorted(safe)
safe=sorted(safe, reverse=True)
for s in safe:
    poplist2.pop(s)#finishes the list of values to pop unused Mirion data points
poplist2=sorted(poplist2, reverse=True)
for p2 in poplist2: #throws out unused Mirion data points
    chMirion.pop(p2)
    tMirion.pop(p2)
    #for cnt in range(count(compindx_Mirion[compindx_Mirion.index(p2)])):#chat says this is just wrong
    #   compindx_Mirion_ip=compindx_Mirion.index(p2)
    #    compindx_Mirion.pop(compindx_Mirion_ip)
    #need to update compindx_Mirion here somehow to be consistent with everything
for cin in range(len(compindx_Mirion)):
    ncomp=compindx_Mirion.count(compindx_Mirion[cin])#counts the number of times a mirion index is used
    if ncomp>1:#checks if it was used multiple times
        minlist=[]
        indx_dup=[]
        for nc in range(ncomp):#checks which data-point is best
            minlist.append(abs(pair[compindx_ORTEC[compindx_ORTEC[nc]]][1]-pair[compindx_ORTEC[compindx_ORTEC[nc]]][0]))#checks all of the time differences with that ORTEC
            indx_dup.append(nc)#all of this stuff in this section is a bit shaky
        safet=min(minlist)
        for pind in range(len(minlist)):
            if minlist[pind]==safet:
                minlistpopv=pind
        indxp=list(range(len(minlist)))
        indxp.pop(minlistpopv)
        for indxpv in indxp:
            poplist3.append(indxpv)#this is the wrong thing to append. I am appending values not indexes here
#chat says there is something wrong with compindx_Mirion not being updated

poplist3=sorted(poplist3, reverse=True)
for p3 in poplist3:
    pair.pop(p3)
    chORTEC.pop(p3)
    tORTEC.pop(p3)
    print(chMirion.index(pair[p3][1]))#chat says the problem is that the thing it is trying to index is a time not a channel
    p3i=chMirion.index(pair[p3][1])#problem right here
    chMirion.pop(p3i)
    tMirion.pop(p3i)
        #unfinished needs work

print("Removing already used pairs")#print statements to figure out where bugs are
#----------------------------------------------------------------

#Pretty sure this stuff is okay
print(len(chORTEC), len(chMirion))#these lengths should be the same at this point, if not something is wrong
print("Finding Energies")
for i in range(len(chORTEC)):#changes channels to Energy
    enORTEC.append(Aortec+Bortec*(chORTEC[i]/2))
for i in range(len(chMirion)):
    enMirion.append(Amirion+Bmirion*(chMirion[i]/2))


if len(chORTEC)!=len(chMirion):
    print("problem with list size")

print("Filtering Energies")
for i in range(len(enORTEC)): 
    if enORTEC[i]+enMirion[i]>1030 or enORTEC[i]+enMirion[i]<1014: #may change the range here of things to keep
        poplist4.append(i)


print("Removing Bad Energies")#print statements to figure out where bugs are
poplist4=sorted(poplist4, reverse=True)
for p4 in poplist4:
    pair.pop(p4)
    difference.pop(p4)#gets rid of the energies that we do not want
print("Graphing")
plt.hist(difference, bins=3000)#plots the histogram

print("finishing")
averagenp5=np.average(difference)#average time difference
standarddevnp5=np.std(difference)#error
print(averagenp5, standarddevnp5)
print(len(tMirion), len(tORTEC))
x=[averagenp5 for i in range(100)]
y=[i for i in range(100)]
plt.plot(x,y)#plots the average on the histogram to see if it is a symetrical distribution