# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 21:58:15 2026

@author: bella
"""


import numpy as np
import matplotlib.pyplot as plt
def checking_en(fileO, fileM):
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
    #enORTEC=[] #list to hold the calibrated energies
    #enMirion=[]
    compindx_ORTEC=[] #list to store values to check if Mirion gets used twice (as the length of the two lists will not be the same)
    compindx_Mirion=[]
   #poplisto=[]
   #poplistm=[]#lists to pop all the necessary indicies at once to prevent changes in idicies when removing variables from a list
   #poplist2=[]
    poplist3=[]
    #poplist4=[]
    pairch=[]
   #safe=[]
    print(2*((-Aortec+511)/Bortec))
    print(Bortec*(16383/2)+Aortec)
    k=0
#--------------------------------------------------------------------------------------
    print("starting analyzation")#print statements to figure out where bugs are
    print(len(chORTEC))
    tORTEC = [tORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
    erORTEC=[erORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
    chORTEC = [chORTEC[i] for i, v, in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]#problem need to figure out better way to do this
    chORTEC = [chORTEC[i] for i, v in enumerate(erORTEC) if v == 0] #enumerate pairs indecies with values
    tORTEC = [tORTEC[i] for i, v in enumerate(erORTEC) if v == 0] #enumerate pairs indecies with values #enumerate pairs indecies with values
    print(len(chORTEC))

    #consider replacing with mask
#extras column stuff
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
    #sorting_o=[list(sorto) for sorto in sorting_o]
    #sorting_m=[list(sortm) for sortm in sorting_m]
    tORTEC=list(sorting_o[:, 0])
    chORTEC=list(sorting_o[:, 1])
    tMirion=list(sorting_m[:, 0])
    chMirion=list(sorting_m[:, 1])
    print(tORTEC[0], tMirion[0])
    print(tORTEC[1], tMirion[1])
    print(tORTEC[2], tMirion[2])
    print(tORTEC[3], tMirion[3])
    for i, to in enumerate(tORTEC):
        while j+1<len(tMirion) and abs(tORTEC[i+k]-tMirion[j])>=abs(tORTEC[i+k]-tMirion[j+1]):
            j+=1
 #THIS PART NEEDS LOVE AND ATTENTION:
        
        if i+k+1<len(tORTEC):
             if abs(tORTEC[i+k]-tMirion[j])<abs(tORTEC[i+k+1]-tMirion[j]) and abs(tORTEC[i+k]-tMirion[j])<abs(tORTEC[i+k-1]-tMirion[j]):
                 if ((((chMirion[j]*0.5)*Bmirion)+Amirion)+(((chORTEC[i]*0.5)*Bortec)+Aortec))<1030 and ((((chMirion[j]*0.5)*Bmirion)+Amirion)+(((chORTEC[i]*0.5)*Bortec)+Aortec))>1014:
                     if  (tORTEC[i+k]-tMirion[j])<0 and (tORTEC[i+k]-tMirion[j])>-100:
                         compindx_ORTEC.append(i+k) #records this index to check it in the future
                         compindx_Mirion.append(j)
                         pair.append([to, tMirion[j]])
                         pairch.append([chORTEC[i+k], chMirion[j]])
                         difference.append(to-tMirion[j])
            #elif abs(tORTEC[i+1+k]-tMirion[j])<abs(tORTEC[i-1+k]-tMirion[j]):
            #    k+=1
            #    compindx_ORTEC.append(i+k) #records this index to check it in the future
            #    compindx_Mirion.append(j)
            #    pair.append([to, tMirion[j]])
            #    pairch.append([chORTEC[i+k], chMirion[j]])
            #    difference.append(to-tMirion[j])
        else:
            #print(tORTEC[i-1+k])
            if abs(tORTEC[i+k]-tMirion[j])<abs(tORTEC[i-1+k]-tMirion[j]):#add energy filter here
                compindx_ORTEC.append(i+k) #records this index to check it in the future
                compindx_Mirion.append(j)
                pair.append([to, tMirion[j]])
                pairch.append([chORTEC[i+k], chMirion[j]])
                difference.append(to-tMirion[j]) 
            break
   
        
    #need to update compindx_Mirion here somehow
####gave up  and let chat write this section
    #seen_mirion = set()#creates a set so no duplicates

    #for cin in range(len(compindx_Mirion)):#
    #    mir_idx = compindx_Mirion[cin]

    #    if mir_idx in seen_mirion:#checks if an index in the Mirion has already been used
    #        continue
    #    seen_mirion.add(mir_idx)#adds this index to the set if not

    #    dup_indices = [i for i in range(len(compindx_Mirion)) if compindx_Mirion[i] == mir_idx]
#
     #   if len(dup_indices) > 1:
     #       best_i = min(dup_indices, key=lambda i: abs(difference[i]))#finds the smallest time difference
     #       for i in dup_indices:
     #           if i != best_i:#keeps the best and gets rid of the rest
     #               poplist3.append(i)

   # poplist3=sorted(poplist3, reverse=True)
#fixed with chat
    #for p3 in poplist3:
    # Remove ORTEC info
    #    pair.pop(p3)
    #    pairch.pop(p3)


#__________________________________________________________________________________
    
    difference=[pair[i][0]-pair[i][1] for i in range(len(pair))]
    print("finishing")
    averagenp5=np.average(difference)
    standarddevnp5=np.std(difference)
    print(averagenp5, standarddevnp5)
    plt.figure()
    plt.hist(difference, bins=300)
    plt.title("10s data")
    def g(z, mu, s):
        return (1/(s*np.sqrt(2*np.pi)))*np.e**(-(z**2)/(2*s**2))
    #xg=np.arange(-400000, 400000)
    #plt.plot(xg, 0.2e6*g(xg, -26, 130887.25))
    plt.figure()
    chMirion=np.array(chMirion)
    plt.hist(chMirion/2, bins=int(max(chMirion)-min(chMirion)))
    plt.title("10s data")
    plt.figure()
    chORTEC=np.array(chORTEC)
    plt.hist(chORTEC/2, bins=int(max(chORTEC)-min(chORTEC)))
    plt.title("10s data")
    return(difference)
    
#d1=checking_en("C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_4thRun_3rd_Attempt_1_19_2026_ch000.txt", "C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_4thRun_3rd_Attempt_1_19_2026_ch001.txt")
d2=checking_en("C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_27hr_2nd_attempt_2_9_2026_ch000.txt", "C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_27hr_2nd_attempt_2_9_2026.txt" )
#checking_en("D:\\Coincidence Doppler Broadening Winter 2026\\Calibration_attempt_and_investigation_2026_ch000.txt", "D:\\Coincidence Doppler Broadening Winter 2026\\Calibration_attempt_and_investigation_2026_ch001.txt")
#d2=checking_en("C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\BackgroundReading_27hr_3rd_Attempt_3_6_2026_ch000.txt", "C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\BackgroundReading_27hr_3rd_Attempt_3_6_2026_ch001.txt")
plt.figure()
plt.hist(d2, bins=300)
xg=np.arange(-400000, 400000, 0.1)
def g(z, a, mu, s):#this was the problem right here
    return (a*np.e**(-(z**2)/(2*s**2)))
#plt.plot(xg, g(xg, 0.18e6, -26, 130887))

histdata, binsdata = np.histogram(d2, bins=300)
for indb in range(len(binsdata)):
    if indb+1==len(binsdata):
        pass
    else:
        binsdata[indb]=(binsdata[indb]+binsdata[indb+1])/2
binsdata=np.array([binsdata[binsdatael] for binsdatael in range(len(binsdata)-1)])
binsdata=[binsdata[binsdata_ind] for binsdata_ind in range(len(histdata)) if histdata[binsdata_ind]!=0]
histdata=[histdata_val for histdata_val in histdata if histdata_val!=0]
histdata=[histdata[binsind] for binsind in range(len(binsdata)) if binsdata[binsind]>-80 and binsdata[binsind]<-20]
binsdata=[binsdata[binsind2] for binsind2 in range(len(binsdata)) if binsdata[binsind2]>-80 and binsdata[binsind2]<-20]
#binsdata=np.array([(binsdata[indb]+binsdata[indb+1])/2 for indb in range(len(binsdata))])
from scipy.optimize import curve_fit
#guess=[35000, -51, 9.995]
#fit2, error2=curve_fit(g,binsdata, histdata,p0=guess)
#print('fit parameters (A,mu,sigma,B) =', fit2)
#uncerts=np.sqrt(np.diag(error2))
#print('with uncertainties =',uncerts)
#X=np.linspace(0,max(binsdata),len(binsdata))
#plt.plot(X,g(X,*fit2),'--r')
#plt.plot(binsdata,histdata,'ob')
#dotx=binsdata[np.where(histdata==max(histdata))]
#doty=max(histdata)
#plt.plot(dotx,doty, 'or')
#plt.show()
#print(np.where(histdata==(max(histdata))))
#print(dotx, binsdata[1]-binsdata[0])

#histdata10s, binsdata10s = np.histogram(d1, bins=300)
#print(sum(histdata10s)/10.28)


#ORTEC=np.loadtxt("C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_4thRun_3rd_Attempt_1_19_2026_ch000.txt", skiprows=5)
#Mirion=np.loadtxt("C:\\Users\\bella\\OneDrive\\Desktop\\PAS Winter 2025 Coincidence Doppler Broadening\\TimeCheck_4thRun_3rd_Attempt_1_19_2026_ch001.txt", skiprows=5)
#chORTEC=ORTEC[:, 1]#extracts the channel columns
#chMirion=Mirion[:, 1] 
#erORTEC=ORTEC[:, 2]#extracts extras columns
#erMirion=Mirion[:, 2]
#tORTEC=ORTEC[:, 0] #extracts time columns
#tMirion=Mirion[:, 0]

#--------------------------------------------------------------------------------------

#tORTEC = [tORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
#erORTEC=[erORTEC[i] for i, v in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]
#chORTEC = [chORTEC[i] for i, v, in enumerate(chORTEC) if v!=16383 and v>10800 and v<11160]#problem need to figure out better way to do this
#chORTEC = [chORTEC[i] for i, v in enumerate(erORTEC) if v == 0] #enumerate pairs indecies with values
#tORTEC = [tORTEC[i] for i, v in enumerate(erORTEC) if v == 0]

#tMirion = [tMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
#erMirion=[erMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
#chMirion = [chMirion[i] for i, v in enumerate(chMirion) if v!=16383 and v>10800 and v<11160]
#chMirion = [chMirion[i] for i, v in enumerate(erMirion) if v == 0] #enumerate pairs indecies with values
#tMirion = [tMirion[i] for i, v in enumerate(erMirion) if v == 0]#enumerate pairs indecies with values

#print(len(chMirion)/10.28)
#print(len(chORTEC)/10.28)