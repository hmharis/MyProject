#!/usr/bin/python

import sys
from comsim import *
import math
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
import json


class Logger(object):

    def log(self, header, text):
        lText = text.split('\n')
        lHeader = [header] + [''] * (len(lText) - 1)
        print('\n'.join(['{0:10} {1}'.format(h, t) \
                for h, t in zip(lHeader, lText)]))

#
#_______________________________________________________________________________
#      
        
        
    
  

def Handshake(flights,listOfTimes,RetransmissionCriteria='exponential', \
        LossRate=9e-3, datarate=500):
    tempDict={}

    #logger = Logger()
    logger = None

    scheduler = Scheduler()

    if RetransmissionCriteria == 'exponential':
        timeouts = lambda i: 1*(2**(i-1)) 
#        timeouts = lambda i: 1*2**i 
    elif RetransmissionCriteria == 'linear':
        timeouts = lambda i: 1*i 
    elif RetransmissionCriteria == 'constant':
        timeouts = lambda i: 1 
    else:
        # No retransmission at all
        timeouts = None

    server=GenericServerAgent(scheduler, 'server1', flights, \
            timeouts=timeouts, logger=logger)
    client=GenericClientAgent( scheduler, 'client1',flights, \
            timeouts=timeouts, logger=logger)

    medium = Medium(scheduler, data_rate=datarate/8, bit_loss_rate=LossRate, \
            inter_msg_time=0.001, logger=logger)
    medium.registerAgent(server)
    medium.registerAgent(client)
    client.trigger()
        
    scheduler.run()

    # Last flight can be received at either Client or Server side 
    if len(flights)%2==0:
            handshaketime=client.doneAtTime
    else:
            handshaketime=server.doneAtTime
        
    # if hanshake was incomplete, don't append 'None' in the list
    if handshaketime != None:           
        listOfTimes.append(handshaketime)


    tempDict['HS-Time']=handshaketime
    tempDict['Total-Data']=client.txCount + server.txCount 
    #tempDict['Server-Data']=server.txCount
    #tempDict['Client-Data']=client.txCount
    Superfluous_Dict=Superfluous_Data(flights,client.nRx,server.nRx)
    tempDict['Superfluous_Messages_List']=Superfluous_Dict['Total_superfluousData_frequency']
    tempDict['SFData']=Superfluous_Dict['SuperFluous_data']
    
    
    tempDict['Retransmissions List'] = [x-1 if x>0 else x for x in map(sum, zip([y for y in client.nTx],[z for z in server.nTx]))]
    tempDict['Total flight Retransmissions']=sum([x-1 if x>0 else x for x in map(sum, zip([y for y in client.nTx],[z for z in server.nTx]))])
 

    return tempDict
#    return handshaketime
    
#
#_______________________________________________________________________________
#

def Superfluous_Data(flights,ClientData,ServerData):

    tempdict={}
    # List of all message lengths 
    msgLength_list=[]


    for elements in flights:
        for values in elements:
            msgLength_list.append(values.getLength())

    #print msgLength_list

    # Client message reception frequency
    clientdata_frequency=[]
    for elements in ClientData:
        for values in elements:
              clientdata_frequency.append(values)

    # Server message reception frequency
    serverdata_frequency=[]
    for elements in ServerData:
        for values in elements:
              serverdata_frequency.append(values)

#    print 'Client Data---',clientdata_frequency
#    print 'Server Data---',serverdata_frequency
    
    # If a message is transmitted more than once, it's Superfluous
#    superfluousData_frequency= [x+y-1 for x,y in zip(clientdata_frequency, \
#            serverdata_frequency)]
    Client_superfluousData_frequency=[x-1 if x>0 else x for x in clientdata_frequency]
    Server_superfluousData_frequency=[x-1 if x>0 else x for x in serverdata_frequency]

    tempdict['Total_superfluousData_frequency']=map(sum,zip(Client_superfluousData_frequency,Server_superfluousData_frequency))

    superfluousData_list= [x*y for x,y in zip(tempdict['Total_superfluousData_frequency'], \
            msgLength_list)]
    #client_superfluouslist=[superfluousData_list[0],superfluousData_list[6],superfluousData_list[7],superfluousData_list[8],superfluousData_list[9],superfluousData_list[10]]
    #server_superfluouslist=[superfluousData_list[1],superfluousData_list[2],superfluousData_list[3],superfluousData_list[4],superfluousData_list[5],superfluousData_list[11],superfluousData_list[12]]
    #print superfluousData_list
    #print client_superfluouslist
    #print server_superfluouslist
    
#    print 'Total Freq----',Total_superfluousData_frequency
#    print 'Total---------',superfluousData_list
    tempdict['SuperFluous_data']=sum(superfluousData_list)
    #tempdict['Client_Data']=sum(client_superfluouslist)
    #tempdict['Server_Data']=sum(server_superfluouslist)

    return tempdict
    

#
#_______________________________________________________________________________
#

def MultipleHandshakes(flights,noOfTimes,listOfTimes,Retransmit='exponential'\
        ,LossRate=0):
    ExportData=[]
    while(noOfTimes):
        noOfTimes-=1
        result=Handshake(flights,listOfTimes,RetransmissionCriteria=Retransmit,\
                LossRate=LossRate)
        ExportData.append(result)
    
    with open('Output_Data','w') as outputfile:
        json.dump(ExportData,outputfile,sort_keys=True,indent=1)


#
#______________________________________________________________________________
#



def calculationsForPlots(flights,RetrasmissionCriteria):
    Loss_Rate=0
    ListOfStats=[]
    mean,var,std,median,OneQuarter,ThreeQuater=([] for i in range(6))

    Loss_Rate_list=[]

    while Loss_Rate<4e-4:
        Loss_Rate+=0.5e-4
        Loss_Rate_list.append(Loss_Rate)
        tmp_list=[]
        MultipleHandshakes(flights,1000,tmp_list,Retransmit=RetrasmissionCriteria, \
                LossRate=Loss_Rate)

        if len(tmp_list)>0:
            mean.append(np.mean(tmp_list))
            var.append(np.var(tmp_list))
            std.append(np.std(tmp_list))
            median.append(np.median(tmp_list))
            OneQuarter.append(np.percentile(tmp_list,25))
            ThreeQuater.append(np.percentile(tmp_list,75))
#        else:
#            mean.append(0)
#            var.append(0)
#            std.append(0)
#            median.append(0)
#            OneQuarter.append(0)
#            ThreeQuater.append(0)
            
    
    ListOfStats=[mean,var,std,median,OneQuarter,ThreeQuater]
    print ListOfStats

    return ListOfStats


#
#_______________________________________________________________________________
#



def plot_All_Handshakes(RetransmissionCriteria,Comparison,*param):
    
    Loss_Rate_list=[0.5e-4,1e-4,1.5e-4,2e-4,2.5e-4,3e-4,3.5e-4,4e-4]
    ylabel=['Mean','Variance','Standard deviation','Median','0.25-Quantile', \
            '0.75-Quantile']

    if Comparison == 0:
        ListOfStats=[]
        counter=len(param)
        while counter > 0:
            templist = []
            templist=calculationsForPlots(param[len(param) - counter], \
                    RetransmissionCriteria)
            ListOfStats.append(templist)

            counter-=1


        drawFigure(6,ylabel,RetransmissionCriteria,Comparison,Loss_Rate_list, \
                ListOfStats)
        


    elif Comparison == 1:

        ListOfAllLists=[]
        
        templist_exp = []
        templist_lin = []
        templist_exp=calculationsForPlots(param[0],'exponential')
        templist_lin=calculationsForPlots(param[0],'linear')

        ListOfAllLists.append(templist_exp)
        ListOfAllLists.append(templist_lin)
      

        drawFigure(6,ylabel,RetransmissionCriteria,Comparison,Loss_Rate_list, \
                ListOfAllLists)
         
#
#_______________________________________________________________________________
#


def drawFigure(NoOfFigs,ylabels,Retranmission_Criteria,Comparison, \
        Loss_Rate,CompleteList):
    count=1
    while count <= NoOfFigs:
        plt.figure(count)
        plt.xlabel('Loss Rate')
        plt.ylabel(ylabels[count-1])
        plt.title('Loss Rate v/s {0}'.format(ylabels[count-1]))

        Flightslen=len(CompleteList)
        i=0
        while(i<Flightslen):
            plt.plot(Loss_Rate,CompleteList[i][count-1],label=ylabels[count-1]+'(Plot:'+str(i+1)+')')
            i+=1

        count+=1
        plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=2, \
                mode="expand", borderaxespad=0.)    
    #plt.show()
#
#_______________________________________________________________________________
#



def plotHistogram(HandshakeTimesList):
    

#    bins = np.linspace(8,1000,10)
    if max(HandshakeTimesList)-min(HandshakeTimesList)>1000:
        plt.xscale('log')
		
    plt.hist(HandshakeTimesList, bins='auto', alpha=0.5, label='1')
    plt.title("Histogram")
    plt.xlabel("Handshaketime")
    plt.ylabel("Frequency")

    plt.show()

#
#_______________________________________________________________________________
#

def ackversion(flightStructure,version):
    if version == 1:
        result=[]
        for element in flightStructure:
            if len(element)==1:
                result.append(element)
            else:
                count=len(element)
                for message in element:
                    count-=1
                    if count == 0:
                        result.append([message])
                    else:
                        result.append([message])
                        result.append([ProtocolMessage('Ack',5)])


        return result

    elif version == 2:
        temp=flightStructure
        temp.append([ProtocolMessage('ACK', 5)])
    return temp
            
                 

    
#
#_______________________________________________________________________________
#


def DRrange(start, end, step):
    while start <= end:
        yield start
        start += step

def HStime_BER_DR_HeatMap_Data(flights, Avg_NoOfHS,MinDR, MaxDR, DRStep, minBER, MaxBER):
    result=[]
    HandshakeList=[]
    DR=MinDR
    BER=minBER
    BERStepCounter=0
    while(BER<=MaxBER):
        row=[]     
        BERStepCounter=BERStepCounter+1   
        for y in DRrange (MinDR, MaxDR,DRStep):
            Values=[]
            x=0
            while (x<Avg_NoOfHS):
                HSTdict=Handshake(flights,HandshakeList,RetransmissionCriteria='exponential',LossRate=BER, datarate = y)
                HST=HSTdict['HS-Time']
                if(HST):
                    Values.append(HST)
                    x=x+1
#                else:
#                    Values.append(0)
            row.append(np.mean(Values))
        result.append(row)
        if (BERStepCounter == 10):
             minBER=minBER*10
             BERStepCounter=0    
        BER=BER+minBER
    print "Result --> ", result
    return result


def plot_BER_vs_FailedHS(minBER, maxBER, NoOfAverages, DR, flights):
    BER = minBER
    BER_Failure_List = []
    BERlist=[]
    BERStepCounter=0
    while(BER <= maxBER):
        print 'New Iteration for BER = ',BER
        BERStepCounter=BERStepCounter+1
        BERlist.append(BER)
        HandshakeList=[]
        Values=[]
        x=1
        N=0
        Failed_HS = []
#        if(BER>1e-4):
#            NoOfAverages = 1000
        while(x<NoOfAverages):
            HSTimedict=Handshake(flights,HandshakeList,RetransmissionCriteria='exponential',LossRate=BER, datarate = DR)
            HSTime=HSTimedict['HS-Time']
            if(HSTime):
                Values.append(HSTime)
                Failed_HS.append(N)   
                x=x+1       
                N=0
            else:
                N=N+1     
        BER_Failure_List.append(sum(Failed_HS)/NoOfAverages)
        if (BERStepCounter == 10):
             minBER=minBER*10
             BERStepCounter=0    
        BER=BER+minBER
    print 'The list of failed handshakes per BER: ', BER_Failure_List
    plt.figure()
    plt.xlabel("BER")
    plt.ylabel("No of Failed Handshakes ")
    plt.plot( BERlist, BER_Failure_List,"r")
    #plt.show()


def average(data):

    withoutNone = [item for item in data if item is not None]
    return float(sum(withoutNone)) / len(withoutNone)

    
def plot_BER_vs_TotalRetransmission(minBER, maxBER, NoOfAverages, DR, flights):
    n=50.0    
    B= (maxBER/minBER)**(1/n)    
    BER = minBER
    Avg_Retransmissions_List_l = []
    Avg_Retransmissions_List_e = []
    Avg_Retransmissions_List_c = []
    BERlist=[]
    BERStepCounter=0
    std_list_l = []
    std_list_e = []
    std_list_c = []
    HSdurationlist_l=[]
    HSdurationlist_e=[]
    HSdurationlist_c=[]
    avghsduration_list_l=[]
    avghsduration_list_e=[]
    avghsduration_list_c=[]
    averagehsduration_list= [0.032,0.052,0.072,0.092,0.114,0.139,0.151,0.175,0.192,0.218,0.475,0.749,1.196,1.641,2.234,3.117,4.032,5.013,6.609,7.686,28.356,44.702,54.914,84.914,104.914,204.914,500.914,1000.914]
    stdlist1_hsduration_l=[]
    stdlist1_hsduration_e=[]
    stdlist1_hsduration_c=[]
    stdlist2_hsduration=[]
   
    while(BER <= maxBER):
        print 'New Iteration for BER = ',BER
        BERStepCounter=BERStepCounter+0.3 
        BERlist.append(BER)
        
        HandshakeList=[]
        Values_l=[]
        Values_e=[]
        Values_c=[]
        
        x=1
#        if(BER>1e-4):
#            NoOfAverages = 1000
        while(x<NoOfAverages):
            #HSdict_l=Handshake(flights,HandshakeList,RetransmissionCriteria='linear',LossRate=BER, datarate = DR)
            HSdict_e=Handshake(flights,HandshakeList,RetransmissionCriteria='exponential',LossRate=BER, datarate = DR)
            #HSdict_c=Handshake(flights,HandshakeList,RetransmissionCriteria='constant',LossRate=BER, datarate = DR)
            #HSTotalFlightRetransmissions_l=HSdict_l['Total flight Retransmissions']
            #HSTotalFlightRetransmissions_e=HSdict_e['Total flight Retransmissions']
            #HSTotalFlightRetransmissions_c=HSdict_c['Total flight Retransmissions']
            #HSTotalFlightDuration_l= HSdict_l['HS-Time']
            HSTotalFlightDuration_e= HSdict_e['HS-Time']
            #HSTotalFlightDuration_c= HSdict_c['HS-Time']
            #Values_l.append(HSTotalFlightRetransmissions_l)
            #Values_e.append(HSTotalFlightRetransmissions_e)
            #Values_c.append(HSTotalFlightRetransmissions_c)
            #if (HSTotalFlightDuration_l!=None):
            #HSdurationlist_l.append(HSTotalFlightDuration_l)
            #if (HSTotalFlightDuration_e!=None):
            HSdurationlist_e.append(HSTotalFlightDuration_e)
            #if (HSTotalFlightDuration_c!=None):
            #HSdurationlist_c.append(HSTotalFlightDuration_c)
            x=x+1   
        #Avg_Retransmissions_List.append(sum(Values)/NoOfAverages)
        Avg_Retransmissions_List_l.append(np.mean(Values_l))
        Avg_Retransmissions_List_e.append(np.mean(Values_e))
        Avg_Retransmissions_List_c.append(np.mean(Values_c))
        avghsduration_list_l.append(average(HSdurationlist_l)) 
        avghsduration_list_e.append(average(HSdurationlist_e))
        avghsduration_list_c.append(average(HSdurationlist_c))     
        std_list_l.append(np.std(Values_l))
        #td_list_e.append(np.std(Values_e))
        #std_list_c.append(np.std(Values_c))
        stdlist1_hsduration_l.append(np.std(avghsduration_list_l))
        stdlist1_hsduration_e.append(np.std(avghsduration_list_e))
        stdlist1_hsduration_c.append(np.std(avghsduration_list_c))
        #stdlist2_hsduration.append(np.std(averagehsduration_list))
       
        #if (BERStepCounter == 10):
             #minBER=minBER*10
             #BERStepCounter=0    
        #BER=BER+minBER
        BER= minBER * (B**BERStepCounter)

  
   
    #print 'The list of average retransmissions per BER: '
    print BERlist
    #print Avg_Retransmissions_List_e
  
    print avghsduration_list_c
    print avghsduration_list_l
    #print std_list_l
    print avghsduration_list_e
    print stdlist1_hsduration_c
    print stdlist1_hsduration_l
    print stdlist1_hsduration_e
    
    
    plt.figure(1)
    plt.xlabel("BER")
    plt.ylabel("Average Number of Retransmissions ")
    plt.semilogx( BERlist, Avg_Retransmissions_List_l, "b*",label='Linear')
    plt.semilogx(BERlist, Avg_Retransmissions_List_e, "g*",label='exponential')
    plt.semilogx(BERlist, Avg_Retransmissions_List_c, "r*",label='Constant')
    plt.legend(loc="upper left")
    #plt.title("BER vs Average Number of Retransmissions")
    plt.errorbar( BERlist, Avg_Retransmissions_List_l, yerr=std_list_l, fmt='o')
    plt.errorbar( BERlist, Avg_Retransmissions_List_e, yerr=std_list_e, fmt='o-')
    plt.errorbar( BERlist, Avg_Retransmissions_List_c, yerr=std_list_c, fmt='o')
    #plt.ylim(0, 600)
    #plt.title("Exponential Backoff")

    #plt.figure(2)
    #plt.xlabel("BER")
    #plt.ylabel("Realtime HSDuration (Sec)")
    #plt.loglog(BERlist, averagehsduration_list,"r+")
    #plt.errorbar( BERlist, averagehsduration_list, yerr=stdlist2_hsduration, fmt='o')
    #plt.ylim(10e-2, 10e2)

    
    plt.figure(2)
    plt.xlabel("BER",fontsize="15")
    plt.ylabel("Average HS Duration (msec)",fontsize="15")
    plt.loglog(BERlist, avghsduration_list_e, "b*",label='Constant')
    plt.loglog(BERlist, avghsduration_list_l,"g*")
    plt.loglog(BERlist, avghsduration_list_c, "r*",label='Linear')
    plt.legend(loc="upper left")
    #plt.title("Exponential Backoff (ECDHE_ECDSA)")
    plt.errorbar( BERlist, avghsduration_list_e, yerr=stdlist1_hsduration_e, fmt='o')
    plt.errorbar( BERlist, avghsduration_list_l, yerr=stdlist1_hsduration_l, fmt='o-')
    plt.errorbar( BERlist, avghsduration_list_c, yerr=stdlist1_hsduration_c, fmt='o')
    plt.xlim(1e-7, 1.606e-4)
    plt.tick_params(labelsize=15)
    
    plt.show(1)
    plt.show(2)


    #plt.show(2)
    #plt.show(3)
  


def plot_BER_vs_TotalRetransmission_per_Flight(minBER, maxBER, NoOfAverages, DR, flights):
    BER = minBER
    Avg_Total_Retransmissions_List = []
    Avg_Retransmissions_List=[]
    BERlist=[]
    BERStepCounter=0
    FailedCounter=0
    FailureList=[]
    dummy=[]
    AccList=[]
    while(BER <= maxBER):
        print 'New Iteration for BER = ',BER
        RetransmissionList=[0] * len(flights)
        BERStepCounter=BERStepCounter+1
        BERlist.append(BER)
        HandshakeList=[]    
        Values=[]
        x=0
#        if(BER>1e-4):
#            NoOfAverages = 1000
        while(x<NoOfAverages):
            HSdict=Handshake(flights,HandshakeList,RetransmissionCriteria='exponential',LossRate=BER, datarate = DR)
            if(HSdict['HS-Time'] == None):
                FailedCounter = FailedCounter+1
            HSTotalFlightRetransmissions=HSdict['Total flight Retransmissions']
            TempRetransmissionlist=HSdict['Retransmissions List']
            Values.append(HSTotalFlightRetransmissions)
            RetransmissionList=map(sum,zip(RetransmissionList,TempRetransmissionlist)) 
            x=x+1   
        FailureList.append(FailedCounter)
        FailedCounter = 0
        Avg_Total_Retransmissions_List.append(sum(Values)/NoOfAverages)
        Avg_Retransmissions_List.append([v*(1.0/NoOfAverages) for v in RetransmissionList])
        if (BERStepCounter == 10):
             minBER=minBER*10
             BERStepCounter=0    
        BER=BER+minBER
    
    
    
    
    
    index=0
    while (index < len(flights)):
        for z in Avg_Retransmissions_List:
            dummy.append(z[index])
        AccList.append(dummy)
        index=index+1
        dummy=[]

#    plt.figure(1)
#    plt.xlabel("BER")
#    plt.ylabel("No of Retransmissions ")
#    legends=[]
#    for t in range(0,len(flights)):
#        plt.semilogx(BERlist,AccList[t])        
#        legends.append("flight "+str(t+1))
#    plt.legend(legends, loc='upper left')
#    plt.show()

    plt.figure(2)
    plt.xlabel("BER")
    plt.ylabel("No of Failed Handshakes")
    plt.semilogx(BERlist,FailureList, linestyle ='--',color='black')
    plt.show()


def plot_BER_vs_superfluousData(minBER, maxBER, NoOfAverages, DR, flights):
    n=50.0    
    B= (maxBER/minBER)**(1/n)    
    BER = minBER    
    BER = minBER
    BERlist=[]
    AccList = []
    dummy = []
    BERStepCounter=0
    Avg_Superfluous_Message_List=[]
    Avg_Totalhandshakeduration=[]
    stdlist1=[]
    Client_Data_List=[]
    Server_Data_List=[]
    Overall_Data=[]
    Avg_Client_Data=[]
    Avg_Server_Data=[]
    Avg_Overall_Data=[]
    
    messageCounter = 0
    for f in flights:
        for m in f:
            messageCounter =  messageCounter +1

    while(BER <= maxBER):
        print 'New Iteration for BER = ',BER
        superfluousMessageList=[0] * messageCounter
        BERStepCounter=BERStepCounter+0.3
        BERlist.append(BER)
        HandshakeList=[]
        Total_Handshakeduration=[]
        x=0
#        if(BER>1e-4):
#            NoOfAverages = 1000
        while(x<NoOfAverages):
            HSdict=Handshake(flights,HandshakeList,RetransmissionCriteria='linear',LossRate=BER, datarate = DR)
            Superfluous_Message_List=HSdict['Superfluous_Messages_List']
            Handshakeduration_List=HSdict['HS-Time']
            OverallData=HSdict['Total-Data']
            Client_Data=HSdict['Client-Data']
            Server_Data=HSdict['Server-Data']
            if (Handshakeduration_List!=None):
                Total_Handshakeduration.append(Handshakeduration_List)
#            TempRetransmissionlist=HSdict['Retransmissions List']
            superfluousMessageList=map(sum,zip(superfluousMessageList,Superfluous_Message_List)) 
            Overall_Data.append(OverallData)
            Client_Data_List.append(Client_Data)
            Server_Data_List.append(Server_Data)
            x=x+1   
        
        Avg_Superfluous_Message_List.append([v*(1.0/NoOfAverages) for v in superfluousMessageList])
        Avg_Totalhandshakeduration.append(np.mean(Total_Handshakeduration))
        Avg_Overall_Data.append(np.mean(Overall_Data))
        Avg_Client_Data.append(np.mean(Client_Data))
        Avg_Server_Data.append(np.mean(Server_Data))
        stdlist1.append(np.std(Avg_Totalhandshakeduration))
        
        #if (BERStepCounter == 10):
             #minBER=minBER*10
             #BERStepCounter=0    
        #BER=BER+minBER
        BER= minBER * (B**BERStepCounter)
    #print Avg_Superfluous_Message_List
    print Avg_Overall_Data
    #print Avg_Client_Data
    #print Avg_Server_Data
   
   
    index=0
    while (index < messageCounter):
        for z in Avg_Superfluous_Message_List:
            dummy.append(z[index])
        AccList.append(dummy)
        index=index+1
        dummy=[]

    legends=[]
    linestyleList = ['--','-','-.',':']
    i=0
    for t in range(0,messageCounter):
        #plt.semilogx(BERlist,AccList[t], linestyle = linestyleList[i])        
        legends.append("Message "+str(t+1))
        if(i == 3):
            i=0
        else:
            i=i+1
    #print "Acclist" ,AccList
        
    #print "Flight 1"
    #print "Message 1:", AccList[0]    

    #print "Flight 2"
    #print "Message 2:", AccList[1]
    #print "Certificate Message", AccList[2]
    #print AccList[3]
    #print AccList[4]
    #print AccList[5]

    #print "Flight 3"
    #print "Certificate:", AccList[6]

 
   # print AccList[7]
    #print AccList[8]
    #print AccList[9]
    #print AccList[10]

    #print "Flight 3"
    #print AccList[11]
    #print AccList[12]
    
   # print BERlist

  
    #print Avg_Totalhandshakeduration
    #print Avg_Totalhandshakeduration[9]
    #print Avg_Totalhandshakeduration[0]
    #print Avg_Totalhandshakeduration[1]
    #print Avg_Totalhandshakeduration[2]
    #print Avg_Totalhandshakeduration[3]    
    #print Avg_Totalhandshakeduration[4]
    #print Avg_Totalhandshakeduration[5]
    #print Avg_Totalhandshakeduration[6]

   
    #print stdlist1
    #print stdlist1[4]
    #print stdlist1[5]
    #print stdlist1[6]   
    #plt.legend(legends, loc='upper left')
    #plt.xlabel("BER")
    #plt.ylabel("No of Superfluous Receptions ")
    #plt.show()

    #fig,ax1=plt.subplots()
   # ax2= ax1.twinx()
  
    #ax1.loglog(BERlist, Avg_Totalhandshakeduration,"r*",label='Handshake Duration')
    #ax1.set_xlabel("BER")
    #ax1.set_ylabel("Handshake Duration (Sec)")
    #ax1.legend(loc="upper left")
    #ax1.set_title("Exponential Backoff (Message 3=834 Bytes)")
  
 
 
    #ax2.loglog(BERlist, AccList[1],"b+", label='Superflous Reception (Message 2)')
    #ax2.set_ylabel("Superflous Reception")
    #ax2.legend(loc="center left")
    #plt.show()

    
    
    
    plt.figure(1)
    plt.xlabel("BER")
    plt.ylabel("Average Superflous Reception ")
    plt.semilogx(BERlist, Avg_Totalhandshakeduration, "b*")
    #plt.semilogx( BERlist, AccList[1],"r+", label="Flight 2-Message.2")
    #plt.semilogx(BERlist, AccList[2], "b+", label= "Flight 2-Msg.3")
    #plt.semilogx(BERlist, AccList[3], "g+", label= "Flight 2-Msg.4")
    #plt.semilogx(BERlist, AccList[4], "m+", label= "Flight 2-Msg.5")
    #plt.semilogx(BERlist, AccList[5], "c+", label= "Flight 2-Msg.6")
    #plt.semilogx(BERlist, AccList[11], "k*", label= "Flight 4-Msg.12")
    #plt.semilogx(BERlist, AccList[12], "y*", label= "Flight 4-Msg.13")
    #plt.semilogx( BERlist, AccList[3],"g-", label="Message 4 ")
    #plt.semilogx(BERlist, AccList[4], "k--", label= "Message 5 ")
    #plt.semilogx(BERlist, AccList[5], "m^", label= "Message 6 ")
    plt.legend(loc="upper left")
    plt.title("Server to Client")
    #plt.loglog(BERlist, AccList[2])
    plt.show()
  
    #plt.figure(2)
    #plt.xlabel("BER")
    #plt.ylabel("Average Superflous Reception ")
    #plt.semilogx( BERlist, AccList[0],"r*", label="Flight 1-Message.1")
    #plt.semilogx(BERlist, AccList[6], "b+", label= "Flight 3-Msg.6")
    #plt.semilogx(BERlist, AccList[7], "g+", label= "Flight 3-Msg.7")
    #plt.semilogx(BERlist, AccList[8], "m+", label= "Flight 3-Msg.8")
    #plt.semilogx(BERlist, AccList[9], "c+", label= "Flight 3-Msg.9")
    #plt.semilogx(BERlist, AccList[10], "k+", label= "Flight 3-Msg.10")
   
    #plt.semilogx( BERlist, AccList[3],"g-", label="Message 4 ")
    #plt.semilogx(BERlist, AccList[4], "k--", label= "Message 5 ")
    #plt.semilogx(BERlist, AccList[5], "m^", label= "Message 6 ")
    #plt.legend(loc="upper left")
    plt.title("Client to Server")
    #plt.loglog(BERlist, AccList[2])
    #plt.show(2)

    #plt.figure(3)
    #plt.xlabel("BER")
    #plt.ylabel("Bytes ")
    #plt.semilogx(BERlist, Avg_Overall_Data,"go",label="Sum")
    #plt.semilogx( BERlist, Avg_Client_Data,"r*", label="Sent by Client")
    #plt.semilogx(BERlist, Avg_Server_Data, "b+", label= "Sent by Server")
    

    #plt.legend(loc="upper left")

 
    #plt.show(3)
    
    


    
def DR_BER_relation(minBER, maxBER, DRstep, BERStepSize,flights):
    DR=32e6
    BER=minBER
#    targerTimes=[0.030, 0.050, 0.070, 0.090, 0.109, 0.130, 0.152, 0.175, 0.200, 0.214]
    targerTimes=[0.214, 0.450, 0.770, 1.010, 1.6, 2.240, 2.9, 3.9, 5, 6.5]
#, 25.3, 42.5]
    i=0
    while(BER <= maxBER):
        AvgHSTime=1000
        while(AvgHSTime > targerTimes[i]):
            HandshakeList=[]
            Values=[]
            x=1
            while(x<5000):
                HSTimedict=Handshake(flights,HandshakeList,RetransmissionCriteria='exponential',LossRate=BER, datarate = DR)
                HSTime=HSTimedict['HS-Time']
                if(HSTime):
                    Values.append(HSTime)
                    x=x+1
#                    print len(Values)
            AvgHSTime=np.mean(Values)
            if(AvgHSTime > targerTimes[i]):
                DR=DR+DRstep
        print BER,' ,', DR,' ,', targerTimes[i], ' ,', AvgHSTime
        if(BERStepSize==1):
            BER=BER*10
        elif(BERStepSize==0):
            BER=BER+minBER
        i=i+1


#####################################amrut added ###################################
def plot_BER_vs_superfluousData_per_HS(minBER, maxBER, NoOfAverages, DR, flights, flight_msg_size):
    BER = minBER
    BERlist=[]
    AccList = []
    dummy = []
    BERStepCounter=0
    Avg_Superfluous_Message_List=[]
    superfluousMessageSizeList = []
    messageCounter = 0
    for f in flights:
        for m in f:
            messageCounter =  messageCounter + 1

    while(BER <= maxBER):
        print 'New Iteration for BER = ',BER
        superfluousMessageList=[0] * messageCounter
        BERStepCounter=BERStepCounter+1
        BERlist.append(BER)
        HandshakeList=[]
        x=0
#        if(BER>1e-4):
#            NoOfAverages = 1000
        while(x<NoOfAverages):
            HSdict=Handshake(flights,HandshakeList,RetransmissionCriteria='exponential',LossRate=BER, datarate = DR)
            Superfluous_Message_List=HSdict['Superfluous_Messages_List']
#            TempRetransmissionlist=HSdict['Retransmissions List']
            superfluousMessageList=map(sum,zip(superfluousMessageList,Superfluous_Message_List)) 
#            print superfluousMessageList
#            print flight_msg_size
            
#            print "\n"
            x=x+1   
        
        superfluousMessageSizeList = np.multiply(superfluousMessageList, flight_msg_size)
        print superfluousMessageSizeList
          
        Avg_Superfluous_Message_List.append(sum([v*(1.0/NoOfAverages) for v in superfluousMessageList]))
        if (BERStepCounter == 10):
             minBER=minBER*10
             BERStepCounter=0    
        BER=BER+minBER
    print Avg_Superfluous_Message_List


#    superfluousMessage_size_List= np.multiply(Avg_Superfluous_Message_List, flight_msg_size)

#    print superfluousMessage_size_List

#    index=0
#    while (index < messageCounter):
#        for z in Avg_Superfluous_Message_List:
#            dummy.append(z[index])
#        AccList.append(dummy)
#        index=index+1
#        dummy=[]

#    legends=[]
#    linestyleList = ['--','-','-.',':']
#    i=0
#    for t in range(0,messageCounter):
#        plt.semilogx(BERlist,AccList[t], linestyle = linestyleList[i])        
#        legends.append("Message "+str(t+1))
#        if(i == 3):
#            i=0
#        else:
#            i=i+1
#    plt.legend(legends, loc='upper left')
    plt.semilogx(BERlist,Avg_Superfluous_Message_List)
    plt.xlabel("BER")
    plt.ylabel("Avg_Superfluous_Message_List")
    #plt.show()


def segmentsize(flights, maxLenPayload, lenHeader):    
    segmentedFlights = []
    residual = []    
    for flight in flights:
        for msg in flight:            
            payloadLen = msg.getLength() - lenHeader            
            segmented = False            
            # Add to-be-acked segments
            iSeg = 0
            while payloadLen >= maxLenPayload:                
                segName = '{}.seg{}'.format(msg.getName(), iSeg)
                segPayloadLen = min(payloadLen, maxLenPayload)                
                residual.append(ProtocolMessage(segName, segPayloadLen + lenHeader))
                segmentedFlights.append(residual)
                residual = []                
                segmentedFlights.append([ProtocolMessage("ACK.{}".format(segName), 5 + lenHeader)])                
                payloadLen -= segPayloadLen
                iSeg += 1
                segmented = True           
             # Add un-acked (residual) message
            if payloadLen > 0:
                if segmented:
                   msgName = '{}.last'.format(msg.getName())
                else:
                   msgName = msg.getName()
                residual.append(ProtocolMessage(msgName, payloadLen + lenHeader))
        segmentedFlights.append(residual)
        residual = []
#    print segmentedFlights    
    return segmentedFlights


def printFlights(flights):

    for i, flight in enumerate(flights):

        for message in flight:
       
            if (i % 2) == 0:
                print('{:>30} ---> {:30}'.format(message.getName(), ''))
            else:
                print('{:>30} <--- {:30}'.format('', message.getName()))



##########################################################amrut end################################################


################################ Phase 2 #############################################
#   1. change number of retransmissions per flight from 7 to 20 and calculate the total retransmissions per HS again

#   2. 

def main(argv):

       
    
    n=100
    
 
      
    flights = [
        [   # C -> S
            ProtocolMessage('ClientHello', 87)
        ],
    ]

    leftover = [   # S -> C
        ProtocolMessage('ServerHello', 107),
    ]

    i = 0
    seg_length = n
    remaining_length = 800
    while remaining_length > 0:

        flights += [
            leftover + [   # S -> C
                    ProtocolMessage('Certificate_seg{}'.format(i), min(seg_length, remaining_length) + 25)
            ],
            [   # C -> S
                    ProtocolMessage('ACK_{}'.format(i), 5)
            ],
        ]
        
        leftover = []
        remaining_length -= min(seg_length, remaining_length)
        i += 1

    flights += [        
        [   # S -> C
            ProtocolMessage('ServerKeyExchange', 165),
            ProtocolMessage('CertificateRequest', 71),
            ProtocolMessage('ServerHelloDone', 25)
        ],
    ]
    j = 0

    seg_length1 = n
    remaining_length1=800
    while remaining_length1 > 0:
            
        flights += [        
            [   # C -> S
                    ProtocolMessage('Certificate_seg{}'.format(j), min(seg_length1, remaining_length1) + 25)
            ],
            [   # S -> C
                    ProtocolMessage('ACK_{}'.format(j), 5)
            ],
        ]
        remaining_length1 -= min(seg_length1, remaining_length1)
        j += 1

    flights += [
        [   # C -> S
            ProtocolMessage('ClientKeyExchange', 91),
            ProtocolMessage('CertificateVerify', 97),
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ],
        [   # S-> C
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ]
    ]
        
    flights_ed=flights
          
        #plot_BER_vs_superfluousData(1e-5, 9e-5, 5.0, 1e6, flights_ed)





        #HandshakeList=[]
#       while(j<100):
            #HSTime=Handshake(flights_ed,HandshakeList,RetransmissionCriteria='linear',LossRate=2e-4, datarate =1e6)
            #HSduration= HSTime['HS-Time']
#            HSdlist.append(HSduration)
#            j+=1
        #avghsdlist.append(np.mean(HSdlist))
#        i+=1
    

        #print 'DataRate:', '  -- HSd :', HSduration
        #hsdlist.append(HSduration)
        #stdlist.append(np.std(hsdlist))
   # print hsdlist
    #print stdlist
    
    

    #print('\n'.join(map(str, flights)))
    #flights_ed=flights
    #print flights_ed

    
    
    
   
        

    flights2_1 = [
        [
            ProtocolMessage('ClientHello', 87)
        ],
        [
            ProtocolMessage('ACK', 5)  
        ],
        [
            ProtocolMessage('ServerHello', 107),
            ProtocolMessage('Certificate', 800),
            ProtocolMessage('ServerKeyExchange', 165),
            ProtocolMessage('CertificateRequest', 71),
            ProtocolMessage('ServerHelloDone', 25)
        ],
        [
            ProtocolMessage('ACK', 5)  
        ],
        [
            ProtocolMessage('Certificate', 800),
            ProtocolMessage('ClientKeyExchange', 91),
            ProtocolMessage('CertificateVerify', 97),
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ],
        [
            ProtocolMessage('ACK', 5)  
        ],
        [
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ]
    ]



    flights1_1 = [
        [
            ProtocolMessage('ClientHello', 87)
        ],
       
        [
            ProtocolMessage('ServerHello', 107),
            ProtocolMessage('Certificate', 800),
            ProtocolMessage('ServerKeyExchange', 165),
            ProtocolMessage('CertificateRequest', 71),
            ProtocolMessage('ServerHelloDone', 25)
        ],
       
        [
            ProtocolMessage('Certificate', 800),
            ProtocolMessage('ClientKeyExchange', 91),
            ProtocolMessage('CertificateVerify', 97),
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ],
        
        [
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ]
    ]
    



    # ECDHE_ECDSA
    flights_ECDSA = [
        [   # C -> S
            ProtocolMessage('ClientHello', 87)
        ],
        [   # S -> C
            ProtocolMessage('ServerHello', 107),
            ProtocolMessage('Certificate', 834),
            ProtocolMessage('ServerKeyExchange', 165),
            ProtocolMessage('CertificateRequest', 71),
            ProtocolMessage('ServerHelloDone', 25)
        ],
        [   # C -> S
            ProtocolMessage('Certificate', 834),
            ProtocolMessage('ClientKeyExchange', 91),
            ProtocolMessage('CertificateVerify', 97),
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 37)
        ],
        [   # S -> C
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 37)
        ]
    ]

# ECDHE_PSK
    flights_ECDPSK = [
        [   # C -> S
            ProtocolMessage('ClientHello', 87)
        ],
        [   # S -> C
            ProtocolMessage('ServerHello', 107),
            ProtocolMessage('ServerKeyExchange', 95),
            ProtocolMessage('ServerHelloDone', 25)
        ],
        [   # C -> S
            ProtocolMessage('ClientKeyExchange', 101),
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 37)
        ],
        [   # S -> C
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 37)
        ]
    ]

# PSK
    flights_PSK = [
        [   # C -> S
            ProtocolMessage('ClientHello', 71)
        ],
        [   # S -> C
            ProtocolMessage('ServerHello', 97),
            ProtocolMessage('ServerHelloDone', 25)
        ],
        [   # C -> S
            ProtocolMessage('ClientKeyExchange', 35),
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 37)
        ],
        [   # S -> C
            ProtocolMessage('ChangeCipherSpec', 14),
            ProtocolMessage('Finished', 37)
        ]
    ]


    

    #j=1
    #while j<50:    
    #HandshakeList=[]
 
    #HSTime=Handshake(flights_ed,HandshakeList,RetransmissionCriteria='linear',LossRate=9e-5, datarate =1e6)
    #HSduration= HSTime['HS-Time']
#            HSdlist.append(HSduration)
#            j+=1
#        avghsdlist.append(np.mean(HSdlist))
#        i+=1
    

    #print 'DataRate:', '  -- HSd :', HSduration
        #hsdlist.append(HSduration)
    #stdlist.append(np.std(hsdlist))
        #print hsdlist
        #j+=1
    #print (np.mean(hsdlist))
    #print stdlist

    flights3_1 = [
        [
            ProtocolMessage('ClientHello', 87)
        ],
        [
            ProtocolMessage('ServerHello', 107),
            ProtocolMessage('Certificate', 800)
        ],
        [
            ProtocolMessage('ACK1', 5)    
        ],

        [
            ProtocolMessage('ServerKeyExchange', 165),
            ProtocolMessage('CertificateRequest', 71),
            ProtocolMessage('ServerHelloDone', 25)
        ],
        [
            ProtocolMessage('Certificate', 800)
        ],
        [
            ProtocolMessage('ACK2', 5)
        ],

        [
            ProtocolMessage('ClientKeyExchange', 91),
            ProtocolMessage('CertificateVerify', 97),
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ],
        [
            ProtocolMessage('ChangeCipherSpec', 13),
            ProtocolMessage('Finished', 37)
        ]

    ]  


    print("\nUnsegmentized")
    printFlights(flights_ECDSA)

    newflights=segmentsize(flights_ECDSA, 400, 25)


    print("\nSegmentized")
    printFlights(newflights)

    #quit()


    flights3_msg_size = [87, 107, 834, 5, 165, 71, 25, 834, 5, 91, 97, 13, 37, 13, 37]

    flights_msg_size = [87, 107, 834, 165, 71, 25, 834, 91, 97, 13, 37, 13, 37]

    #BERlist= [1e-06, 2e-06, 3e-06, 4e-06, 4.9999999999999996e-06, 5.999999999999999e-06, 6.999999999999999e-06, 8e-06, 9e-06, 1e-05, 1.9999999999999998e-05, 2.9999999999999997e-05,                3.9999999999999996e-05,    4.9999999999999996e-05, 5.9999999999999995e-05, 7e-05, 7.999999999999999e-05, 8.999999999999999e-05, 9.999999999999999e-05, 0.00010999999999999999, 0.00020999999999999998,  0.00030999999999999995, 0.00040999999999999994, 0.0005099999999999999, 0.0006099999999999999, 0.0007099999999999999, 0.00081, 0.00091]

#   Finding out Datarate required to reach 5% more of the lowest possible Handshake Time (12ms)
#    DR=1e9
#    i=0
    
    #HSdlist=[]
    #avghsdlist=[]
#   
#    while(i<len(BERlist)):
    Avg_hslist=[]
    std_hslist=[]
    HSlist=[]
    HandshakeList=[]
    minBER=1e-7
    maxBER=1e-3

    segSizeList = range(10, 800, 100)
    BERlist = [3*1E-4, 2*1E-4, 1E-4, 1E-5, 1E-6, 1E-7, 0]
       
    data = {}

    for segSize in segSizeList:

        segmentizedHandshake = segmentsize(flights_ECDSA, segSize, 25)

        for BER in BERlist:

            if BER not in data:
                data[BER] = {}

            HSlist = []

            for iteration in range(500):

                print('Iteration {} with segment size {} and BER {}'.format(iteration, segSize, BER))
                HSTime = Handshake(segmentizedHandshake, HandshakeList, RetransmissionCriteria='linear', LossRate=BER, datarate =10e3)
                HSduration= HSTime['HS-Time']
                HSlist.append(HSduration)

            mean = np.mean(HSlist)
            std = np.std(HSlist)

            data[BER][segSize] = (mean, std)

    for BER in data.keys():

        X = segSizeList
        Y = [data[BER][segSize][0] for segSize in segSizeList]
        Yerr = [data[BER][segSize][1] for segSize in segSizeList]

#        plt.plot(X, Y, "k-*",label='BER = {}'.format(BER))
        plt.errorbar(X, Y, yerr=Yerr, fmt='-*' , label='BER={}'.format(BER))

    plt.xlabel('Maximum Segment Size [octets]')
    plt.ylabel('Average Handshake Duration [s]')
    plt.legend(loc='upper left')
    plt.show()


    #print(data)
    quit()
          
                        
        #minBER*=10
        #if minBER==1e-4:
        #    k=1
        #    while(k<=3):
        #        minBER=1e-4
        #        k+=1
            
            
    #BER=BER+1    
    #print Avg_hslist
    #print std_hslist
    #SFdata=HSTime['SFData']
    #csfdata=HSTime['ClientSFData']
    #ssfdata=HSTime['ServerSFData']
    #totaldata=HSTime['Total-Data']
    #serverdata=HSTime['Server-Data']
    #clientdata=HSTime['Client-Data']
    #sflist=HSTime['Superfluous_Messages_List']
        #HSdlist.append(HSduration)
#            j+=1
        #avghsdlist.append(np.mean(HSdlist))
#        i+=1
    
    Segsize=[10,100,200,300,400,500,600,700,800]

    
      
    plt.plot(Segsize, Avg_hslist[0:9], "k-*",label='BER 1e-4')
    plt.plot(Segsize, Avg_hslist[9:18], "r-*",label='BER 1e-5')
    plt.plot(Segsize, Avg_hslist[18:27], "g-*",label='BER 1e-6')
    plt.plot(Segsize, Avg_hslist[27:36], "b-*",label='BER 1e-7')
    plt.plot(Segsize,Avg_hslist[36:45], "y-*", label='BER 3*1e-4')
    plt.xlabel('Seg Size (octets)')
    plt.ylabel('Average Handshake Duration(msec)')
    plt.legend(loc='upper right')

    
    plt.errorbar(Segsize, Avg_hslist[0:9], yerr=std_hslist[0:9],fmt='k*' )
    plt.errorbar(Segsize, Avg_hslist[9:18], yerr=std_hslist[9:18],fmt='r*' )
    plt.errorbar(Segsize, Avg_hslist[18:27], yerr=std_hslist[18:27],fmt='g*' )
    plt.errorbar(Segsize, Avg_hslist[27:36], yerr=std_hslist[27:36],fmt='b*')
    plt.errorbar(Segsize, Avg_hslist[36:45], yerr=std_hslist[36:45],fmt='y*')
    plt.show()

    



    




    #print Avg_hslist
    #plt.plot(Segsize,
    #hslist_7=[0.047,0.037
    #hslist_6=[0.077,0.078
    #hslist_5=[0.259,0.119
    #hslist_4=[2.328,2.111
    #print 'DataRate:', '  -- HSd :', HSduration,'--SFdata:',totaldata,serverdata,clientdata
    
    #BERlist=[1e-7, 2e-7, 3e-7,4e-7,5e-7,6e-7,7e-7,8e-7,9e-7,1e-6,2e-6,3e-6,4e-6,5e-6,6e-6,7e-6,8e-6,9e-6,1e-5,2e-5,3e-5,4e-5,5e-5,6e-5,7e-5,8e-5,9e-5,1e-4]
    #total_data=[2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,2343,3511,3511,3511,6805,6885,6885,7923,8183,9091]
    #server_data= [1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0,1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0, 1218.0,1218,2386,2386,2386,4722,4722,7058,5890]
    #client_data=[1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0,1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0, 1125.0,1125.0,1125,1125,1125,1125,3201,1125,2163,3201,3201]  
    #plt.semilogx(BERlist,total_data,"r*",label="Sum")
    #plt.semilogx(BERlist,server_data,"b",label="Sent by Server")
    #plt.semilogx(BERlist,client_data,"go",label="Sent by Client")
    #plt.xlabel("BER")
    #plt.ylabel("Bytes") 
    #plt.legend(loc="upper left")
    #plt.show()
#SFdata: 3511 2386 1125
#8831 3554 5277

#13763 10562 3201

#14023 12898 1125
#42833 38594 4239
#492941 202214 290727
#252590 10562 242028
    


    




#   Finding out Datarate required to reach 5% more of the lowest possible Handshake Time (12ms)
#    DR="inf"
#    HSTime=10
#    while(HSTime>=0.0126):

#Certificate Size Analysis

    #HandshakeList=[]
    #HSTime=Handshake(flights,HandshakeList,RetransmissionCriteria='linear',LossRate=0, datarate =1e6)
    #print HSTime
    #BER_list=[  7.000000000000001e-05, 8e-05, 9e-05, 0.0001, 0.0002, 0.00030000000000000003, 0.0004, 0.0005, 0.0006000000000000001, 0.0007000000000000001]
    

    #BER0_HSD=[]

#Seg vs HSDuration

    #Seg_length=[8,16,24,32,40,48,56,64,72,80,88,96,104,112,120,128,136,144,152,160,168,176,184,192,200,208,216,224,232,240,248,256,264,272,280,288,296,304,312,320,328,336,344,352,360,368,376,384,392,400,408,416,424,432,440,448,456,464,472,480,488,496,504,512,520,528,536,544,552,560,568,576,584,592,600,608,616,624,632,640,648,656,664,672,680,688,696,704,712,720,728,736,744,752,760,768,776,784,792,800]

    
    #BER=[1e-07, 2e-07, 3e-07, 4e-07, 5e-07, 6e-07, 7e-07, 8e-07, 9e-07, 1e-06, 2e-06, 3e-06, 4e-06, 5e-06, 6e-06, 7e-06,  8e-06, 9e-06,1e-05,2e-05,3e-05,4e-05,5e-05,6e-05,7e-05,8e-05,9e-05]
    #hsd_1=[0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000006, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000006, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001, 0.39388000000000001]
    #hsd_100=[0.065048, 0.065048, 0.065048, 0.065048, 0.065048, 0.065048, 0.065048, 0.065048, 0.065048, 0.065048, 0.065048, 0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048,0.065048]
    #plt.semilogx(BER,hsd_1, label="1 iteration")
    #plt.semilogx(BER,hsd_100, "r*")
    #plt.xlabel('BER')
    #plt.ylabel('Avg HS Duration(msec)')
   
    #plt.title("Linear Backoff (Bandwidth=1Mbps)")
    #plt.legend(loc="upper left")
    
    #plt.show()  

    #Seg_Size=[

 

    




    #Seg_length=[1,100,200,300,400,500,600,700,800] 
    
    
    #BER_0=[7.224087999999957, 0.12776800000000002, 0.10088799999999998, 0.08296799999999997, 0.08296799999999997, 0.07400799999999999, 0.07400799999999999, 0.074008, 0.074008]
    #BER1_3=[141.96779200000915, 106.071704, 66.05412000000001, 640.0441680000001, 1455.0463840000004, 3523.023768, 37193.05045600004, 55981.043416, 191926.037536]


    #BER1_4=[8.220839999999956, 0.12776800000000002, 0.10088799999999998, 0.08296799999999997, 0.08296799999999997, 0.077079999999997, 0.0834959999999996, 0.074008, 0.074008]


    #BER1_5=[7.224087999999957, 0.12776800000000002, 0.10088799999999998, 0.08296799999999997, 0.08296799999999997, 0.07400799999999999, 0.07400799999999999, 0.074008, 0.074008]


    #BER1_6=[7.224087999999957, 0.12776800000000002, 0.10088799999999998, 0.08296799999999997, 0.08296799999999997, 0.07400799999999999, 0.07400799999999999, 0.074008, 0.074008]



    #BER1_7=[7.224087999999957, 0.12776800000000002, 0.10088799999999998, 0.08296799999999997, 0.08296799999999997, 0.07400799999999999, 0.07400799999999999, 0.074008, 0.074008]


    

  

    #std_0=[0.0, 3.5481599999999789, 3.3515909707480516, 3.0831840414739902, 2.8502231797415272, 2.6573886597351177, 2.4963203076528311, 2.3600733439450425, 2.2432449306361155]

    #std1_3=[0.0, 17.948044000004579, 31.006848274796805, 233.36185228122449, 529.48126551138807, 1232.1458491146038, 12720.13756145644, 20323.684225869769, 59588.111227406545]

    #std1_4=[0.0, 4.0465359999999784, 3.6091901291467754, 3.3956157370933293, 3.1732022878656396, 4.4701811786779002, 4.2215901115310697, 4.0740958360174764, 3.930425086732896]

    #std1_5=[0.0, 3.5481599999999789, 3.3515909707480516, 3.0831840414739902, 2.8502231797415272, 2.6573886597351177, 2.4963203076528311, 2.3600733439450425, 2.2432449306361155]

    #std1_6=[0.0, 3.5481599999999789, 3.3515909707480516, 3.0831840414739902, 2.8502231797415272, 2.6573886597351177, 2.4963203076528311, 2.3600733439450425, 2.2432449306361155]

    #std1_7=[0.0, 3.5481599999999789, 3.3515909707480516, 3.0831840414739902, 2.8502231797415272, 2.6573886597351177, 2.4963203076528311, 2.3600733439450425, 2.2432449306361155]

    #plt.semilogy(Seg_length,BER_0,"k-*",label='BER=0')
    #plt.semilogy(Seg_length,BER1_3,"r-*",label='BER=1e-3')
    #plt.semilogy(Seg_length,BER1_4,"b-*",label='BER=1e-4')
    #plt.semilogy(Seg_length,BER1_5,"g-*",label='BER=1e-5')
    #plt.semilogy(Seg_length,BER1_6,"y-*",label='BER=1e-6')
    #plt.semilogy(Seg_length,BER1_7,"c-*",label='BER=1e-7')
    #plt.errorbar(Seg_length,BER_0,yerr=std_0,fmt='r*')
    #plt.errorbar(Seg_length,BER1_3,yerr=std1_3,fmt='b*')
    #plt.errorbar(Seg_length,BER1_4,yerr=std1_4,fmt='g*')
    #plt.errorbar(Seg_length,BER1_5,yerr=std1_5,fmt='y*')
    #plt.errorbar(Seg_length,BER1_6,yerr=std1_6,fmt='c*')
    #plt.errorbar(Seg_length,BER1_7,yerr=std1_7,fmt='m*')
   
    #plt.xlabel('Segment Length (Bytes)')
    #plt.ylabel('Avg HS Duration(msec)')
    #plt.legend(loc="upper right")
    #plt.title("Linear Backoff (Bandwidth=1Mbps)")
    
    #plt.show()  
    










    #BER0=[86.9277999999962,4.5597999999999965, 4.143799999999999, 4.0398, 3.9357999999999995, 4.361799999999999, 4.4418, 4.521799999999999, 4.7096]
    #BER1_4=[87.878,4.039,4.303,4.733,4.738,4.774,5.144,6.8102,7.549]


    #BER2_4=[88.430,5.210,5.279,6.008,6.097,8.146,8.206,9.486,17.688]


    #BER3_4=[95.145,5.905,7.356,13.684,15.097,17.524,18.417,20.918,21.623]


    #BER4_4=[98.483,8.519,7.674,23.021,26.274,38.159,40.927,99.485,501.151]



    #BER5_4=[111.424,20.450,16.590,41.927, 92.119,99.691,422.012,705.914,715.440]


    #BER6_4=[ 115.283,10.756,57.867, 95.926,96.877,203.295,884.715,2917.711,6630.293]


    #BER7_4=[130.287,20.680,29.799,158.412,168.619,587.979,910.212, 6761.982,12595.213]

    #std1_4=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

    #std2_4=[0.276,0.328,0.487,0.634,0.661,0.799,2.053,2.376,6.271]

    #std3_4=[3.303,0.575,1.272,3.656,4.563,5.724,5.885,6.153,7.026]

    #std4_4=[4.492,1.378,1.409,7.210,8.806,12.890,14.269,38.159,210.675]

    #std5_4=[8.575,5.795,4.360,13.395,32.353,35.211,162.171,270.908,298.585]

    #std6_4=[10.558,5.325,18.918,31.357,71.234,39.965,328.222,1054.025,2392.548]

    #std7_4=[14.562,6.316,18.121,53.098,76.409,193.994,386.068,2358.293,4526.2253]
    
  
  

    #plt.semilogy(Seg_length,BER0,"k-*",label='BER=0')
    #plt.semilogy(Seg_length,BER1_4,"r-*",label='BER=1e-4')
    #plt.semilogy(Seg_length,BER2_4,"b-*",label='BER=2e-4')
    #plt.semilogy(Seg_length,BER3_4,"g-*",label='BER=3e-4')
    #plt.semilogy(Seg_length,BER4_4,"y-*",label='BER=4e-4')
   # plt.semilogy(Seg_length,BER5_4,"c-*",label='BER=5e-4')
    #plt.semilogy(Seg_length,BER6_4,"m-*",label='BER=6e-4')
    #plt.semilogy(Seg_length,BER7_4,"k-*",label='BER=7e-4')
    #plt.semilogy(Seg_length,BER9_5,"b-*",label='BER=9e-5')
    #plt.semilogy(Seg_length,BER8_5,"k-*",label='BER8e-5')
   # plt.errorbar(Seg_length,BER1_4,yerr=std1_4,fmt='r*')
   ## plt.errorbar(Seg_length,BER2_4,yerr=std2_4,fmt='b*')
   # plt.errorbar(Seg_length,BER3_4,yerr=std3_4,fmt='g*')
    #plt.errorbar(Seg_length,BER4_4,yerr=std4_4,fmt='y*')
    #plt.errorbar(Seg_length,BER5_4,yerr=std5_4,fmt='c*')
    #plt.errorbar(Seg_length,BER6_4,yerr=std6_4,fmt='m*')
    #plt.errorbar(Seg_length,BER7_4,yerr=std7_4,fmt='k*')
    #plt.xlabel('Segment Length (Bytes)')
    #plt.ylabel('Avg HS Duration(msec)')
    #plt.legend(loc="upper right")
   # plt.title("Linear Backoff (Bandwidth=10Kbps)")
    
    #plt.show()  
    


 
    

    #Seg_Num=[1,10,20,30,40,50,60,70,80,90,100]    
    #Ber0_HSD=[]
    #Ber9_5_HSD=[]
    #Ber1_4_HSD=[4.491804000000001,3.1710736000000019,3.1555397600000021,3.7299736799999939,4.1642233599999985,4.9683833599999989,4.8132277599999984,6.3368050399999811,6.8512062079999998,6.885909759999989,7.1406239999999892]
    #Ber2_4_HSD=[1621.9400209600008,5.7293927199999963,6.5431984799999965,7.6771729067199974, 8.6811410399999946,9.6548635200000064,11.338438880079986,11.642860125759974,13.736585407999979,13.300441297919999,15.68366680000001]
    #Ber3_4_HSD=[25738560.379548043,10.117352399999993,11.440739599999988,11.964014186719997,16.197227199999983,16.280797600000032,18.724350213439983,19.577185017279987,20.281365328,22.534472888960025,25.227502799999982]
    #Ber4_4_HSD=[7.9267150418087517e+26,17.725509200000001,16.818719999999985,21.321208320160011,20.684619919999982,24.247019200000025,26.319819626720001,26.612515737280038,28.706097968000044,31.288898275840005,37.162480799999969]
    #Ber5_4_HSD=[9.5790324914596968e+51,36.043954879999994,31.126548799999981,32.847891920480023, 28.411207759999961,32.463825200000066,37.406773306720012,40.60854995456009,46.581004528000065,41.803460746880063,53.646535280000023]
    #Ber6_4_HSD=[2.4104070663895159e+58,46.83283208000001,86.393636079999993,37.096768800480021,45.678668959999932,53.279782240000024,54.279782240000024,56.83428526880013,58.976881328000196,63.689541600640069,65.250666560000219]
    #Ber7_4_HSD=[4.149515568880993e+178,82.661411520000016,97.342416639999968,63.573587387040014,60.54494528,77.797312720000164,122.62864021352009,1388.4903528460889,5552.851107408000232,22208.851107408000232,88832.851107408000232]
    

    #plt.semilogy(Seg_Num,Ber1_4_HSD,"r-*",label='BER=1e-4')
    #plt.semilogy(Seg_Num,Ber2_4_HSD,"b-*",label='BER=2e-4')
    #plt.semilogy(Seg_Num,Ber3_4_HSD,"g-*",label='BER=3e-4')
    #plt.semilogy(Seg_Num,Ber4_4_HSD,"y-*",label='BER=4e-4')
    #plt.semilogy(Seg_Num,Ber5_4_HSD,"c-*",label='BER=5e-4')
    #plt.semilogy(Seg_Num,Ber6_4_HSD,"m-*",label='BER=6e-4')
    #plt.semilogy(Seg_Num,Ber7_4_HSD,"k-*",label='BER=7e-4')
    #plt.xlabel('No of Segments')
    #plt.ylabel('Avg HS Duration(msec)')
    #plt.legend(loc="upper right")
    #plt.title("Exponential Backoff")
    #plt.show()
   



 #Seg=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]    
    #HSD_0=[0.0307,0.0370,0.0413,0.0455,0.0479,0.0540,0.0582,0.0625,0.0677,0.0709]
    #HSD_1e6=[0.060714,0.047054,0.06128384,0.075514,0.059774,0.07400336,0.068253984,0.072494,0.086723888,0.100954]
    #HSD_1e5=[0.32030824,0.266854,0.21116384,0.2453174,0.279574,0.28379336,0.328033984,0.372194,0.286533888,0.27077104]
    #HSD_1e4=[4.63859672,2.98495936,3.00965416,2.51355684,2.13806864,2.3620730144,2.49639032688,2.59028496,2.44467774584,2.71871736]
    #plt.semilogy(Seg,HSD_0)
    #plt.semilogy(Seg,HSD_1e6)
    #plt.semilogy(Seg,HSD_1e5)
    #plt.semilogy(Seg,HSD_1e4,"r",label='BER = 1e-4')
    #HSD_0=[0.0307,0.0370,0.0413,0.0455,0.0479,0.0540,0.0582,0.0625,0.0677,0.0709, 0.075383952, 0.079623872,0.083863904,0.088103808,0.09234392]
    #HSD_1e6=[0.060714,0.047054,0.06128384,0.075514,0.059774,0.07400336,0.068253984,0.072494,0.086723888,0.100954]
    #HSD_1e5=[0.32030824,0.266854,0.21116384,0.2453174,0.279574,0.28379336,0.328033984,0.372194,0.286533888,0.27077104]
    #HSD_4e4=[1.01003276865e+17,97669.1021938,450.236184288,134.62974744,44.13478824,28.318419115,35.0329801948,24.07734376,21.9615279968,25.66520224,18.0400785341,19.0844969125,17.8283634549
#,20.4627560826,16.9368409869]
    #HSD_5e4=[5.02168138831e+56,688928142.661,1596.63514314,362.91875872,86.84309376,44.167066635,52.1615041604,40.83573296,44.2095232237,26.58488944,33.4379600541,36.5326282192,29.4468974858
#,30.3709534998,26.4250884269]
    #HSD_6e4=[4.80981520952e+109,13109187784.7,43083680.3942,1576.6677256,191.29181456,122.735646155,89.2903146408,68.2342776,45.0188595526,64.50241008,60.3366382941,99.5905916595,182.264534692
#,41.4190609858,67.4640654402]
    #HSD_7e4=[1.31503397539e+208,5.90318474156e+18,5501977849.72, 4617.87719536, 549.9515584, 156.875488208, 92.0094145492, 154.6133252, 110.516825393, 177.25095112, 73.6556143741, 174.669134593,          71.7033752832,57.417817523,53.7516791204]
    #Std_4e4=[4.37357017142e+16,583882.176594,100.632439399,29.8549582126,9.89208309297,5.50874650068,7.64592600063,6.43669815688,5.21545299858,5.3980594227,5.35440678201,5.97876394731, 3.85179435099,4.7943109926,4.07915164926]
    #Std_5e4=[2.00867255532e+56,4253509.10247,4567.92771085,148.664562846,26.0116284812,12.8220771037,9.9567395719,8.97057586106,7.13170580579,7.05982896403,7.62105113003,7.34235402733, 8.38669347631,8.09103340107,7.25528892976]
    #Std_6e4=[1.79251229462e+109,32783941750.6,250580.223599,198.217475869,58.285822455,23.3499082638,19.9529345129, 53.0407846357,15.5146464423,16.7479515471,31.9360372559, 11.099979796, 10.2407929777, 14.3747920028,13.8442173951]
    #Std_7e4=[inf5.72724051297e+147,5.04513608358e+15,121262641.188,436.191013842,149.462365254,79.553108232,62.656588183,51.2886609902,20.2667157444,61.443123165,37.2897093532,21.9113877187, 22.5271736254,24.3239889261,27.3246288167]
    #plt.semilogy(Seg,HSD_0,"b*",label='BER=0')
    #plt.semilogy(Seg,HSD_4e4,"k",label='BER=4e-4')
    #plt.semilogy(Seg,HSD_5e4,"g",label='BER=5e-4')
    #plt.semilogy(Seg,HSD_6e4,"y",label='BER=6e-4')
    #plt.semilogy(Seg,HSD_7e4,"c",label='BER=7e-4')
    #plt.errorbar(Seg,HSD_4e4,yerr=Std_4e4,fmt="k*")
    #plt.errorbar(Seg,HSD_5e4,yerr=Std_5e4,fmt="g*")
    #plt.errorbar(Seg,HSD_6e4,yerr=Std_6e4,fmt="y*")
    #plt.errorbar(Seg,HSD_7e4,yerr=Std_7e4,fmt="c*")
    #plt.xlabel('No of Segments')
    ##plt.ylabel('Avg HS Duration(msec)')
    #plt.legend(loc="center")
    #plt.title("Exponential Backoff")
    #plt.show()

#Linear Scenario

    #Seg_Num=[1,10,20,30,40,50,60,70,80,90,100]    
    #BER0_HSD=[0.065048,0.145688,0.235288,0.32488736,0.414488,0.504088,0.59368736, 0.68328672,0.772983936,0.86248544,0.952088]
    #BER9_5_HSD=[1.4896173600000002,0.2154855199999999,0.43437655999999891,0.42447930751999796,0.55389928000000055,0.67352951999999744,0.76291074720000007,0.88280923488000122,1.31252278943999732,1.6717125792000004,2.8416388000000121]
    #BER1_4_HSD=[5.8624094400000057,0.36474512000000003,0.45458959999999971,0.49405906783999759,0.67330256000000044,0.71346807999999728,0.9426309605600004,1.3107497283199958,1.9107497283199958,2.916072639999981,3.9112048000000086]
    #BER2_4_HSD=[13.55013383999999,1.3511386400000018,1.0617354399999994,1.1418068033599982,1.3208521600000014,1.3808370399999973,1.6807146151999977, 2.1478112511999985,2.759925242879995,3.7889762912000002,4.8188188799999927]
    #BER3_4_HSD=[51.044985200000028,2.7982333600000002,2.3295549600000003,2.1484068343999922,2.8189474400000011,3.3673652799999997,4.4058149643999899,5.4949242271999969,6.3161442295999985,7.5951352320000077,9.62535335999999853]
    #BER4_4_HSD=[309.22123152000006,4.9529774399999988,4.3451763999999988, 4.0959575579199945,4.6854044799999985, 5.5034639200000003,6.8130484600799893,8.8396292380799784,10.462534016799995, 12.4718091225600022,14.7700649599999796]
    #BER5_4_HSD=[1523.4182545600006,7.3191354399999957,6.2997088799999981,7.4104488438399956, 7.815399537599999906,9.5983456800000067, 10.7770057179999865,12.4950380204799698,14.417347003840006,16.605509097599997,18.855654399999983]
    #BER6_4_HSD=[5537.4462569599982,12.473775439999999,10.055812559999987,9.3869327683199941,10.3863441599999905,12.5534352000000222,14.6552558894159996,16.6951156015679977,20.950623750079978,24.9504314572799908,28.957529199999981]
    #BER7_4_HSD=[21386.455284960015,19.409104320000012,14.151936799999994,15.38082536352,17.410367599999972,19.4149371440000014, 21.61347379858799979,24.774530047999946,28.8574371617599978,31.913280520319988,35.926039071999999]
    
    #plt.semilogy(Seg_Num,BER0_HSD,"m-+",label='BER=0')
    #plt.semilogy(Seg_Num,BER9_5_HSD,"k-+",label='BER=9e-5')    
    #plt.semilogy(Seg_Num,BER1_4_HSD,"r-*",label='BER=1e-4')
    #plt.semilogy(Seg_Num,BER2_4_HSD,"b-*",label='BER=2e-4')
    #plt.semilogy(Seg_Num,BER3_4_HSD,"g-*",label='BER=3e-4')
    #plt.semilogy(Seg_Num,BER4_4_HSD,"y-*",label='BER=4e-4')
    #plt.semilogy(Seg_Num,BER5_4_HSD,"c-*",label='BER=5e-4')
    #plt.semilogy(Seg_Num,BER6_4_HSD,"m-*",label='BER=6e-4')
    #plt.semilogy(Seg_Num,BER7_4_HSD,"k-*",label='BER=7e-4')
    #plt.xlabel('No of Segments')
    #plt.ylabel('Avg HS Duration(msec)')
    #plt.legend(loc="upper right")
    #plt.title("Linear Backoff")
    #plt.show()



    #HSD_0=[0.060088,0.072728,0.08120768,0.089688,0.098168,0.10664672,0.115127968,0.123608,0.132087776,0.140568]    
    #HSD_4e4=[401.736998,25.28216784,13.7329403632,9.1941048,5.85491152,5.7648736208,4.793261936,4.28218786,3.94328663152,3.56130192]
    #HSD_5e4=[1302.08597288,67.98956088,22.4295784816,14.75022048,12.2395612,8.5997988496,8.05905013128,7.72845462,8.44688885064,6.72565488]
    #HSD_6e4=[5639.3150424,153.775454,37.235774016,27.00530724,16.96737336,17.3644781296,13.7544073439,10.4659349,12.1736787394,10.02197768]
    #HSD_7e4=[22018.8042582,272.24208736,85.8915587992,46.0706486,31.30975192,27.5994437232,20.1495586135,15.48033766,16.8390211289,15.37725064]
    #Std_4e4=[164.409782047,9.64302008818,5.08250360872,3.43719006336,2.08314251655,2.04503739928,1.69459809471,1.52945665402,1.44017806811,1.28291283216]
    #Std_5e4=[495.479609511,24.4252008848,8.11746961448,5.35570388755,4.2540024654,3.02059531054,2.82075847052,2.66683728103,2.9230006487,2.32229596165]
    #Std_6e4=[2020.34044703,53.8374309086,12.8765024214,9.23604980767,6.02947310301,5.76086813733,4.66979320626,3.65519935582,4.278587395,3.4590999229]
    #Std_7e4=[7509.03269077,94.0855018793,27.9370005642,15.3957598405,10.2761827969,9.23508463974,6.82891910854,5.15449391817,5.80945773614,5.13397482326]
    #plt.semilogy(Seg,HSD_0,"b-*",label='BER=0')
    #plt.semilogy(Seg,HSD_4e4,"k-*",label='BER=4e-4')
    #plt.semilogy(Seg,HSD_5e4,"g-*",label='BER=5e-4')
    #plt.semilogy(Seg,HSD_6e4,"y-*",label='BER=6e-4')
    #plt.semilogy(Seg,HSD_7e4,"c-*",label='BER=7e-4')
    #plt.errorbar(Seg,HSD_4e4,yerr=Std_4e4,fmt="k-*")
    #plt.errorbar(Seg,HSD_5e4,yerr=Std_5e4,fmt="g-*")
    #plt.errorbar(Seg,HSD_6e4,yerr=Std_6e4,fmt="y-*")
    #plt.errorbar(Seg,HSD_7e4,yerr=Std_7e4,fmt="c-*")
    #plt.xlabel('No of Segments')
    #plt.ylabel('Avg HS Duration(msec)')
    #plt.legend(loc="upper right")
    #plt.title("Linear Backoff")
    #plt.show()

#Constant Scenario

    
    #HSD_4e4=[29.04353984,12.42318832,11.1464900552,11.07987372,9.90416088,9.7883096288,10.0521882813,9.61651884,9.78018417288,9.37450048]
    #HSD_5e4=[53.693784,20.3325904,14.7857289632,14.68952296,13.18324712,12.787310512,12.9109597784,12.48509924,12.039570635,11.7534324]
    #HSD_6e4=[107.23365792,27.31217584,20.6554761624,17.4787126,16.60256512,15.196616512,15.690150167,14.94436644,15.5281916042,15.73209144]
    #HSD_7e4=[210.18345344,37.42202448,24.1751624832,23.83828092,19.88201336,19.9153992352,19.5290213671,19.41339328,19.4371026891,18.69081992]
    #Std_4e4=[10.3887945759,3.78090489109,3.43089288736,3.26274535235,2.85690328463,2.76923070519,2.97043809226,2.69818358093,2.79427604328,2.6652910367]
    #Std_5e4=[18.9438145451,6.29995937186,4.52842326251,4.49514852969,3.86661081758,3.70167669695,3.85388484738,3.59212089298,3.51728534297,3.33117501366]
    #Std_6e4=[36.6008083438,8.72624867321,6.23655235877,5.45083019038,4.92683780338,4.48454661224,4.69999576723,4.37730754003,4.49433667944,4.42678226825]
    #Std_7e4=[70.0120556249,11.8528484666,7.56346095063,7.12711444143,5.96065203882,5.73630283187,5.7651620999,5.57792048712,5.65428235403,5.4237733507]
    #plt.semilogy(Seg,HSD_0,"b-*",label='BER=0')
    #plt.semilogy(Seg,HSD_4e4,"k-*",label='BER=4e-4')
    #plt.semilogy(Seg,HSD_5e4,"g-*",label='BER=5e-4')
    #plt.semilogy(Seg,HSD_6e4,"y-*",label='BER=6e-4')
    #plt.semilogy(Seg,HSD_7e4,"c-*",label='BER=7e-4')
    #plt.errorbar(Seg,HSD_4e4,yerr=Std_4e4,fmt="k-*")
    #plt.errorbar(Seg,HSD_5e4,yerr=Std_5e4,fmt="g-*")
    #plt.errorbar(Seg,HSD_6e4,yerr=Std_6e4,fmt="y-*")
    #plt.errorbar(Seg,HSD_7e4,yerr=Std_7e4,fmt="c-*")
    #plt.xlabel('No of Segments')
    #plt.ylabel('Avg HS Duration(msec)')
    #plt.legend(loc="upper right")
    #plt.title("Constant Backoff")
    #plt.show()




    
#Linear Scenario

    
    


    

    



    #linear_list_200=[7.020144, 10.020143999999998, 23.014056, 46.014056, 106.02014400000002, 106.02014400000002, 106.02014400000002]
    #linear_std_list200_err=[1.0077750998979322, 1.2329854157306772, 1.760070214069092, 2.4829178670624827, 2.7610700471603375, 3.1018161029330313, 3.8777881708323312]


    #linear_list_400=[12.017256, 28.023344, 171.023344, 235.017256, 328.01828000000006, 907.019576, 2344.01596]
    #linear_std_list400_err=[1.2942701380649659, 1.981549421123856, 3.3318025257516446, 4.4663829522164153, 6.9519903905842995, 9.5843842997803943, 14.159750017536561]


    #linear_list_600=[0.84800439999999955, 4.758791200000001, 36.510442640000015, 84.298124240000021, 214.81410856000005, 925.82241447999968, 1843.4614383199985]

    #linear_std_list600_err=[0.84800439999999955, 4.758791200000001, 36.510442640000015, 84.298124240000021, 214.81410856000005, 925.82241447999968, 1843.4614383199985]

    #linear_list_600_mult=[0.77668024000000035, 4.9095139199999922, 20.891099679999989, 76.758447199999964, 300.24518695999984, 696.93197624000084, 1369.3821459200005]


    #stdlist_600_mult=[0.0, 2.066416839999996, 8.6735950962230852, 30.345654455989557, 113.07047627484181, 251.78018859717218, 475.98600479953438]


  
    #linear_list_800=[ 0.45535968000000038, 1.7015682400000005, 1.2410622399999989, 2.1590695999999996, 14.188241519999993, 83.272327520000033, 409.71692208000007, 1383.7848969600018, 6286.9343407200031, 23113.794838079961]
    #stdlist_800=[0.0, 0.019543120000000039, 0.044431588866389059, 0.13459419090947433, 0.13511511147197125, 0.15498964273239255, 0.15954190663306958, 0.49182831991897663, 0.5244178252676106, 0.69356701157997047, 3.9309331933670992, 22.793396265352406, 109.07625609373937, 361.79555352959301, 1573.7248062666622, 5671.4033635715896]

    #linear_list_800=[1.1708167199999984, 18.049447600000004, 66.240449840000039, 373.62759047999998, 992.57589768000116, 5483.4248191199968, 23748.234438879968]
    

    #stdlist_800=[0.0, 8.4393154400000032, 27.570753489180408, 151.34563841505786, 376.3120110570855, 1965.6024195585626, 8112.4323895589841]

    #linear_list_800_mult=[1.5287458399999994, 13.55852552, 81.351944479999972, 363.00839776000032, 1330.2666259199987, 5116.1742916799903, 19164.624038880025]

    #stdlist_800_mult=[0.0, 6.0148898400000004, 35.138466251477986, 146.46362942928494, 503.50239137496209, 1831.887855209467, 6527.6368083609459]

    #linear_list_800_ack=[1.9581727199999994, 11.569771599999999, 68.904227519999978, 267.02042232000019, 1033.4488225599996, 3761.0150689599982, 11055.065401360003]

    #stdlist_800_ack=[0.0, 4.8057994400000004, 29.554839652485263, 106.83645640658933, 390.31233537739223, 1346.567038914623, 3779.9695941285258]

    #linear_list_800_seg_ack= [0.21796439999999973, 1.3641888000000006, 3.5690224000000006, 7.0353139199999974, 14.60002184, 27.794911679999995, 40.909950000000009]
    #stdlist_800_seg_ack= [0.0, 0.57311220000000052, 1.3906318027831941, 2.5987713780310133, 5.1729929821517349, 9.6032796358726404, 14.246936359528231]


    #BER_list=[0.001,0.002,0.003,0.004,0.005,0.0001, 0.0002, 0.00030000000000000003, 0.0004, 0.0005, 0.0006000000000000001, 0.0007000000000000001]
    #BER_list=[1e-06, 2e-06, 3e-06, 4e-06, 5e-06, 6e-06, 7e-06, 8e-06, 9e-06, 1e-05, 2e-05, 3e-05,4e-05,5e-05, 6e-05, 7e-05, 8e-05, 9e-05,1e-4,2e-4,3e-4,4e-4,5e-4,6e-4,7e-4,8e-4,9e-4,1e-3,2e-3,3e-3,4e-3,5e-3]

    #linear_800= [1.2510323999999977, 14.567856319999992, 111.02157295999987, 273.64705392000013, 1174.6657962400004, 5893.3340124800006, 23379.124517119966]
    #packet_loss_800=[0.0064, 0.0128,0.0191,0.0253,0.0315,0.0377, 0.0439,0.05,0.056,0.062,0.1202,0.1747,0.2259,0.2739,0.3189,0.3612,0.4008,0.4379,0.4728,0.722, 0.8535, 0.9228, 0.9535, 0.9786, 0.9887,0.9984,0.9999,0.999,0.999,0.999,0.999,0.999]
    #packet_loss_400=[0.0032,0.0064,0.0096,0.0128,0.0159,0.0191,0.0222,0.0253,0.0284,0.0315,0.062,0.0916,0.1202,0.1479,0.1747,0.2007,0.2259,0.2506,0.2739,0.4728,0.6172,0.7221,0.7982,0.8535,0.8937,0.9228,0.944,0.9594,0.9983,0.99999,0.9999,0.9999]
    
    #packet_loss_200=[0.0016,0.0032,0.0048,0.0064,0.0080,0.0096,0.0112,0.0128,0.0143,0.0159,0.0315,0.0469,0.062,0.07689,0.0916,0.106,0.1202,0.1342,0.1479,0.2739,0.3183,0.4728,0.5508,0.6173,0.6739,0.7221,0.7633,0.7983,0.9594,0.9919,0.9984,0.9996]
    #packet_loss.append(1-(1-BER_list)**8)
    #print packet_loss
    #plt.semilogx(BER_list, packet_loss_800, "b*",label='Packet Size 800')
    #plt.semilogx(BER_list,packet_loss_400, "r+",label='Packet Size 400')
   # plt.semilogx(BER_list,packet_loss_200, "k^",label='Packet Size 200')
   # plt.xlabel("BER")
   # plt.ylabel("Packet Loss Prob")
    #plt.legend(loc="upper left")
    #plt.show()
    


    #linear_800_std=[0.0, 6.6584119599999969, 48.910608742230799, 108.77123328753906, 440.69046483841333, 2117.4774293913106, 7989.6612027587225]







    
#Exp Case

    #exp_list_800=[14.727931439999963, 418.76624823999975, 537627574.42442465, 2.5353012004566036e+28, 1.4965776766268446e+49, 5.5993618554451469e+99, 6.7039039649712987e+151]
    #exp_list_800_std=[0.0, 202.0191583999999, 253439966.9100863, 1.0978176229203011e+28, 5.9863107065073785e+48, 2.0867589565657833e+99, 2.3458777141143819e+151]


    #exp_list_200=[7.020143999999999, 11.014055999999998, 512.0163760000002, 512.0163760000002, 4194310.014056, 4194310.014056, 4194310.014056]
    #exp_std_list200_err=[0.94291725495878487, 1.3693483063872729, 1.9729318166287484, 2.6079783093724012, 4.3224298320616636, 3.2200524660150176, 4.3187931518351199]

    #exp_list_400=[8.017256, 1038.0172559999999, 1038.0172559999999, 2097407.017256, 536870913.017256, 70368744179710.0, 1.8889465931753455e+22]
    #exp_std_list400_err=[1.0625763325059503, 2.4238636067662096, 2.9493565762477294, 4.7112090015298937, 6.8897182474193803, 11.28405354026474, 15.635541439506333]

    #exp_list_600=[128.01916000000003, 1038.0204559999997, 32767.026543999993, 536870926.01336, 2.8823917224473395e+17, 3.777893186295716e+22, 7.410693711188237e+78]
    #exp_std_list600_err=[1.6257292556550063, 2.8128366093389912, 4.5631529740727856, 8.286732265472839, 17.574555862783694, 26.305093869308184, 60.977799329094211]

    #exp_list_800=[270.0236560000001, 262398.02365600003, 34359738370.02367, 1.0141204801825835e+31, 3.5681192317649e+44, 7.339195571168229e+106, 1.3597132616109238e+185]
    #exp_std_list800_err=[2.2246543164893526, 4.8429471742860475, 8.8105246354923192, 16.853304545236231, 43.525764722449303, 113.34049384102819, 171.26796622090055]

 
#Constant Case
    #cons_list_200=[4.016376, 6.016376, 10.014055999999998, 14.017944, 20.016376, 22.014056, 23.01508]
    #cons_std_list200_err=[1.0383916990623356, 1.3913751850675922, 2.0904454665812557, 2.7222175371485711, 3.2862918791345721, 3.4845703299911497, 4.7161874689651873]

    #cons_list_400=[4.019576, 8.017256000000001, 18.015960000000003, 22.017256000000003, 35.017255999999996, 58.017255999999996, 59.017255999999996]
    #cons_std_list400_err=[1.1104681335201465, 2.0163599829542087, 3.525845801138614, 4.4373910973730739, 6.7165413238028728, 9.0882936754054811, 12.617928562649308]

    #cons_list_600=[8.020456000000001, 24.020456, 28.020456, 56.020455999999996, 89.02045600000001, 133.020456, 232.02045600000002]
    #cons_std_list600_err=[1.4863937537491805, 3.5496679904699651, 5.6301692909059824, 9.8465732410503239, 16.17578923993959, 26.889033080231744, 49.913536095968091]

    #cons_list_800=[10.025976, 25.023656000000003, 48.02365599999999, 80.023656, 169.02365600000002, 278.0236560000001, 1009.0223599999999]
    #cons_std_list800_err=[1.9931522399063577, 5.4390351869538351, 9.0986947581176629, 17.108189081835359, 33.044703869625486, 66.835792513457534, 158.26869203890624]



    #plt.figure(1)
   #plt.xlabel("BER")
    #plt.ylabel("Simulated Average HS Duration (msec)")
    #plt.loglog(BER_list, linear_list_200,"b*", label='200 Bytes')
    #plt.loglog(BER_list, linear_list_400,"g+", label='400 Bytes')
    #plt.loglog(BER_list, linear_list_600,"ro", label='600 Bytes')
    #plt.loglog(BER_list, linear_list_600_mult,"b+", label='Segmented Scenario(200 bytes*4)')
    #plt.loglog(BER_list, linear_list_800,"k^", label='Non-Segmented Scenario')
    #plt.semilogx(BER_list, linear_list_800_ack,"g*", label='Non-Segmented Ack Scenario')
    #plt.semilogx(BER_list, linear_list_800_mult,"b+", label='Segmented Scenario without Ack')
    #plt.semilogx(BER_list, linear_list_800_seg_ack,"ro", label='Segmented Scenario with Ack')
    #plt.semilogy(BER_list, linear_800,"k^",label='Linear Backoff')
    #plt.errorbar(BER_list,linear_800,yerr=linear_800_std,fmt="k^")
    #plt.loglog(BER_list, linear_list_800,"g*", label='Linear Backoff')
    #plt.legend(loc="upper left")
    #plt.title("Certificate Message (800 Bytes) Analysis for Linear Case")
    #plt.errorbar( BER_list, linear_list_200, yerr=linear_std_list200_err, fmt='b*')
    #plt.errorbar( BER_list, linear_list_400, yerr=linear_std_list400_err, fmt='g+')
    #plt.errorbar( BER_list, linear_list_600, yerr=linear_std_list600_err, fmt='ro')
    #plt.errorbar( BER_list, linear_list_600_mult, yerr=stdlist_600_mult, fmt='ro')
    #plt.errorbar( BER_list, linear_list_800, yerr=stdlist_800, fmt='k^')
    #plt.errorbar( BER_list, linear_list_800_mult, yerr=stdlist_800_mult, fmt='b+')
    #plt.errorbar( BER_list, linear_list_800_ack, yerr=stdlist_800_ack, fmt='g*')
    #plt.errorbar( BER_list, linear_list_800_seg_ack, yerr=stdlist_800_seg_ack, fmt='ro')
    #plt.ylim(10e0, 10e4)
   

    #plt.figure(2)
    #plt.xlabel("BER")
    #plt.ylabel("Simulated Average HS Duration (msec)")
    #plt.loglog(BER_list, exp_list_200,"b*", label='200 Bytes')
    #plt.loglog(BER_list, exp_list_400,"g+", label='400 Bytes')
    #plt.loglog(BER_list, exp_list_600,"ro", label='600 Bytes')
    #plt.loglog(BER_list, exp_list_800,"k^", label='800 Bytes')
    #plt.legend(loc="upper left")
    #plt.title("Certificate Message Analysis for Exponential Case")
    #plt.errorbar( BER_list, exp_list_200, yerr=exp_std_list200_err, fmt='b*')
    #plt.errorbar( BER_list, exp_list_400, yerr=exp_std_list400_err, fmt='g+')
    #plt.errorbar( BER_list, exp_list_600, yerr=exp_std_list600_err, fmt='ro')
    #plt.errorbar( BER_list, exp_list_800, yerr=exp_std_list800_err, fmt='k^')
    #plt.semilogy(BER_list, exp_list_800,"r*",label='Exponential Backoff')
    #plt.errorbar(BER_list, exp_list_800, yerr=exp_list_800,fmt="r*")
    #plt.loglog(BER_list, linear_list_800,"g*", label='Exponential Backoff')
    #plt.legend(loc="upper left")
    #plt.show()


    #plt.figure(3)
    #plt.xlabel("BER")
    #plt.ylabel("Simulated Average HS Duration (Sec)")
    #plt.loglog(BER_list, cons_list_200,"b*", label='200 Bytes')
    #plt.loglog(BER_list, cons_list_400,"g+", label='400 Bytes')
    #plt.loglog(BER_list, cons_list_600,"ro", label='600 Bytes')
    #plt.loglog(BER_list, cons_list_800,"k^", label='800 Bytes')
    #plt.legend(loc="upper left")
    #plt.title("Certificate Message Analysis for Constant Case")
    #plt.errorbar( BER_list, cons_list_200, yerr=cons_std_list200_err, fmt='b*')
    #plt.errorbar( BER_list, cons_list_400, yerr=cons_std_list400_err, fmt='g+')
    #plt.errorbar( BER_list, cons_list_600, yerr=cons_std_list600_err, fmt='ro')
    #plt.errorbar( BER_list, cons_list_800, yerr=cons_std_list800_err, fmt='k^')
    #plt.show(3)




#        DR=DR+1e3
#    print '  -- HS :', HSTime 
#xvalues = [1e-7, 2e-7, 3e-7, 4e-7, 5e-7, 6e-7, 7e-7, 8e-7, 9e-7, 1e-6, 2e-6, 3e-6, 4e-6, 5e-6, 6e-6, 7e-6, 8e-6, 9e-6, 1e-5, 2e-5, 3e-5, 4e-5, 5e-5, 6e-5, 7e-5, 8e-5, 9e-5, 1e-4, 2e-4, 3e-4, 4e-4, 5e-4]
#yvalues = [1, 2, 3]
#yvalues = [0.013, 0.016, 0.018, 0.021, 0.023, 0.025, 0.024, 0.027, 0.027, 0.032, 0.052, 0.072, 0.092, 0.114, 0.139, 0.151, 0.175, 0.192, 0.218, 0.475, 0.749, 1.196, 1.641, 2.234, 3.117, 4.032, 5.013, 6.609, 7.686, 28.356, 44.702, 54.914]
#plt.semilogx(xvalues, yvalues)
#plt.xlabel("BER")
#plt.ylabel("Handshake Duration in Seconds")
#plt.show()


#For Testing BER vs HSDuration for Certificate Message Size

#HS_duration_200=[0.021144000000000003, 1.0201440000000002, 1.0201440000000002, 1.0201440000000002, 1.0201440000000002, 1.021144, 2.014056000000001, 1.0201440000000002, 2.011456000000001, 1.0201440000000002, 1.021144, 4.020143999999999, 3.0201440000000006, 8.016375999999998, 4.016376, 8.011455999999999, 8.014055999999998, 8.01276, 16.020144000000002, 6.011456, 66.01664799999999, 1024.0140559999998, 1026.0163759999998, 2054.01508, 16414.014055999996, 65599.017944]

#HS_duration_300=[1.0227440000000003, 1.0217440000000004, 1.0217440000000004, 1.0227440000000003, 3.0217440000000004, 1.0227440000000003, 1.0227440000000003, 1.0217440000000004, 2.015656000000001, 1.0227440000000003, 4.017976, 7.021743999999999, 3.0217440000000004, 3.0217440000000004, 7.021743999999999, 7.021743999999999, 8.015655999999998, 15.021743999999998, 8.015655999999998, 63.021743999999984, 64.01668, 4102.0156560000005, 8192.015656, 32774.01565600001, 67108864.01954398, 16777343.015656]

    #BERlist=[1e-07, 1.0423174293933042e-07, 1.0864256236170655e-07, 1.132400363235557e-07, 1.1803206356517296e-07, 1.2302687708123815e-07, 1.2823305826560217e-07, 1.3365955165464424e-07, 1.3931568029453033e-07, 1.4521116175877425e-07, 1.5135612484362083e-07, 1.5776112696993487e-07, 1.6443717232149318e-07, 1.7139573075084254e-07, 1.7864875748520508e-07, 1.8620871366628677e-07, 1.9408858775927784e-07, 2.0230191786782718e-07, 2.1086281499332897e-07, 2.197859872784825e-07, 2.290867652767773e-07, 2.387811282913178e-07, 2.488857318282391e-07, 2.5941793621188143e-07, 2.703958364108844e-07, 2.818382931264454e-07, 2.937649651961531e-07, 3.0619634336906776e-07, 3.191537855100762e-07, 3.326595532940047e-07, 3.467368504525318e-07, 3.6140986263961356e-07, 3.767037989839092e-07, 3.926449353996002e-07, 4.0926065973001133e-07, 4.265795188015931e-07, 4.4463126746910926e-07, 4.634469197362887e-07, 4.830588020397733e-07, 5.035006087879056e-07, 5.248074602497735e-07, 5.470159628939725e-07, 5.701642722807486e-07, 5.942921586155739e-07, 6.194410750767828e-07, 6.45654229034657e-07, 6.729766562843194e-07, 7.01455298419973e-07, 7.311390834834194e-07, 7.620790100254141e-07, 7.943282347242838e-07, 8.279421637123366e-07, 8.629785477669729e-07, 8.994975815300382e-07, 9.375620069258834e-07, 9.77237220955814e-07, 1.0185913880541205e-06, 1.0616955571987286e-06, 1.1066237839776705e-06, 1.1534532578210968e-06, 1.2022644346174178e-06, 1.2531411749414212e-06, 1.3061708881318472e-06, 1.361444682465956e-06, 1.4190575216890986e-06, 1.4791083881682143e-06, 1.5417004529495666e-06, 1.606941253012885e-06, 1.6749428760264456e-06, 1.7458221529205128e-06, 1.819700858609993e-06, 1.8967059212111564e-06, 1.9769696401118717e-06, 2.060629913270012e-06, 2.147830474130546e-06, 2.238721138568353e-06, 2.333458062281016e-06, 2.43220400907383e-06, 2.535128630497923e-06, 2.6424087573219634e-06, 2.754228703338184e-06, 2.8707805820247094e-06, 2.992264636608209e-06, 3.1188895840939582e-06, 3.2508729738543663e-06, 3.3884415613920495e-06, 3.5318316979195948e-06, 3.681289736425341e-06, 3.8370724549228165e-06, 3.999447497611005e-06, 4.168693834703385e-06, 4.345102241715749e-06, 4.528975799036243e-06, 4.720630412635942e-06, 4.920395356814549e-06, 5.1286138399136904e-06, 5.345643593969761e-06, 5.571857489319345e-06, 5.80764417521317e-06, 6.053408747539188e-06, 6.309573444801988e-06, 6.576578373554264e-06, 6.854882264526678e-06, 7.144963260755199e-06, 7.447319739059959e-06, 7.762471166286989e-06, 8.0909589917839e-06, 8.43334757764283e-06, 8.79022516830892e-06, 9.162204901220074e-06, 9.549925860214437e-06, 9.954054173515346e-06, 1.0375284158180201e-05, 1.0814339512979456e-05, 1.1271974561755178e-05, 1.1748975549395367e-05, 1.2246161992650557e-05, 1.2764388088113507e-05, 1.3304544179780978e-05, 1.386755828871895e-05, 1.4454397707459338e-05, 1.5066070661867478e-05, 1.570362804333558e-05, 1.6368165214278137e-05, 1.7060823890031285e-05, 1.778279410038927e-05, 1.8535316234148152e-05, 1.9319683170169272e-05, 2.0137242498623907e-05, 2.098939883623526e-05, 2.1877616239495536e-05, 2.2803420720004186e-05, 2.376840286624876e-05, 2.4774220576332837e-05, 2.5822601906345937e-05, 2.6915348039269123e-05, 2.8054336379517085e-05, 2.924152377843329e-05, 3.0478949896279752e-05, 3.1768740706497614e-05, 3.3113112148259e-05, 3.45143739335855e-05, 3.5974933515574085e-05, 3.749730022454819e-05, 3.9084089579240016e-05, 4.0738027780411064e-05, 4.246195639463105e-05, 4.42588372362624e-05, 4.613175745603765e-05, 4.808393484497254e-05, 5.011872336272688e-05, 5.22396188999116e-05, 5.445026528424169e-05, 5.675446054085425e-05, 5.915616341754689e-05, 6.165950018614767e-05, 6.426877173170137e-05, 6.6988460941652e-05, 6.982324040771644e-05, 7.277798045368165e-05, 7.585775750291757e-05, 7.906786279998164e-05, 8.241381150129929e-05, 8.590135215053855e-05, 8.95364765549583e-05, 9.332543007969793e-05, 9.727472237769525e-05]
    


    #avghsduration_list_l=[0.06120000000000009, 0.06119999999999993, 0.061199999999999775, 0.0611999999999997, 0.06119999999999966, 0.06119999999999963, 0.06119999999999961, 0.061199999999999595, 0.06119999999999958, 0.06119999999999957, 0.06119999999999957, 0.06119999999999956, 0.06119999999999955, 0.061199999999999546, 0.061199999999999546, 0.06119999999999954, 0.06119999999999954, 0.06119999999999953, 0.06119999999999953, 0.061199999999999526, 0.061199999999999526, 0.06120000000000009, 0.061200000000000684, 0.061200000000001226, 0.061200000000001725, 0.06120000000000218, 0.061200000000002606, 0.061200000000003, 0.06120000000000337, 0.06120000000000372, 0.061200000000004036, 0.06120000000000434, 0.061200000000004626, 0.06120000000000489, 0.06120000000000514, 0.061200000000005375, 0.06120065738466298, 0.06120064008506695, 0.061200623672629684, 0.06120060808081428, 0.06120059324957525, 0.06120057912458569, 0.061200565656571886, 0.061200552800740375, 0.06120054051627915, 0.06120052876592493, 0.06120051751558579, 0.061200506734010784, 0.06120049639250005, 0.06120048646464976, 0.06120047692612693, 0.061200467754470356, 0.061200458928914035, 0.06120045043023017, 0.061200442240589355, 0.06120043434343571, 0.061200426723375174, 0.06120041936607535, 0.06120041225817552, 0.06120040538720568, 0.06120039874151354, 0.06120039231019857, 0.061200386083052324, 0.061200380050504405, 0.06120037420357334, 0.061200368533822005, 0.06120036303331698, 0.06120035769459151, 0.06120035251061171, 0.06120034747474562, 0.06120034258073491, 0.06120033782266894, 0.061200333194960946, 0.06120032869232614, 0.0612003243097616, 0.0612003200425277, 0.06120031588613104, 0.06120031183630866, 0.06120030788901343, 0.061200304040400576, 0.0612003002868152, 0.06120029662478069, 0.061200293050987974, 0.06120028956228556, 0.06120028615567027, 0.061200282828278586, 0.06120027957737866, 0.061200276400362824, 0.061200273294740606, 0.06130922648708845, 0.06130829348428868, 0.06130711638119842, 0.061305964592153116, 0.06141069331613501, 0.06140847549175449, 0.0614068106060553, 0.06140467853795149, 0.06150265182436062, 0.06159985878991382, 0.06159586020201453, 0.061592181618156064, 0.06168447454940989, 0.061871345689902886, 0.06186489044288445, 0.061858558152952076, 0.061852345340188235, 0.061846248654765776, 0.06193217358772283, 0.06201542025761571, 0.06209715335169235, 0.06208907088906436, 0.06225624098123438, 0.0622468937159136, 0.062411226652483096, 0.06240090575317723, 0.06256045280389423, 0.06289035103167746, 0.06287632734120174, 0.06302805738052096, 0.06309443164982458, 0.06315981701309914, 0.06314375293922116, 0.06369918239302881, 0.06383815835776396, 0.06381705309090173, 0.06395278371010964, 0.06424194003021605, 0.06453128914140666, 0.0645824120272417, 0.06478722486401726, 0.06513595188525724, 0.06563690970308385, 0.06597934229512406, 0.06660938941654586, 0.06693428627010073, 0.0674003778966054, 0.06807869232469911, 0.06932344137021616, 0.06983196860692481, 0.07019478499277712, 0.07126606948921053, 0.07182491051357866, 0.07335865112664344, 0.07451624971940927, 0.07586264130964165, 0.07678313823162544, 0.07906086992372172, 0.08116855473654992, 0.08196219971526926, 0.08475281670033284, 0.08818447735634154, 0.08978574109515933, 0.09168106687792725, 0.09440554217499482, 0.09728145089605586, 0.10140997513597398, 0.10491247918677143, 0.11071701879554996, 0.11601362556381407, 0.12035847474747492, 0.1244151562833308, 0.1315879725651589, 0.1402911064014395, 0.1486922616408006, 0.15672584609733992, 0.16383369696970046, 0.17435939611686113]

    #plt.plot(BERlist,avghsduration_list_l)
    #plt.show()


    
   
    
    

    


#   The following code calculates the datarate required for reaching 0.126 ms (5% more than the minimum handshake time) for different BERs
#   Case 1: BER between 10^-20 and 10^-6 with a large BERStepSize
#   DR_BER_relation(1e-20, 1e-5, 1e4, 1,flights)
#   Case 2: BER between 10^-6 and 10^-5 with a small BERStepSize
#    DR_BER_relation(1e-6, 1e-5, 1e5, 0,flights)
#   Case 3: BER between 10^-5 and 10^-4 with a small BERStepSize
#    DR_BER_relation(1e-5, 1e-4, 2*1e5, 0,flights)
#   Case 4: BER between 10^-4 and 10^-3 with a small BERStepSize
    #DR_BER_relation(2*1e-4, 1e-3, 1e6, 0,flights)

#   Finding the relation between the BER and the average number of failed handshakes per iteration
#   plot_BER_vs_FailedHS(1e-7, 1e-3,10000.0, 1e6, flights)

#   Finding the realation between the BER and the average number of retransmissions per iteration
    #plot_BER_vs_TotalRetransmission(1e-5, 2e-4, 1000.0, 1e6, flights_ECDSA)
    #plot_BER_vs_TotalRetransmission(1e-7, 2e-4, 1000.0, 1e6, flights_ECDPSK)
    #plot_BER_vs_TotalRetransmission(1e-7, 1e-4, 1000.0, 1e6, flights_PSK)

#   Finding the relation between the BER and the average number of retransmissions per flight
#    plot_BER_vs_TotalRetransmission_per_Flight(1e-7, 1e-3, 10000.0, 1e6, flights_PSK)

#   Finding the relation between BER and Superfluous Data (superfluous messages and the total size of redundant data)
#    plot_BER_vs_superfluousData(1e-7, 1e-4, 100.0, 10e6, flights1_1)

#   Finding the realation between the BER and the average number of retransmissions per iteration with unlimited timeout timer
#   We used the same TotalRetransmission function but we modified the retransmission time-out timer to be 20 times
#    plot_BER_vs_TotalRetransmission(1e-7, 1e-3, 10000.0, 1e6, flights)


#--------------------------------------------------------------------------------------------------------------
#    mylist=[]
#    data=Handshake(flights,mylist,RetransmissionCriteria='exponential', \
#            LossRate=0, datarate=1000000000)
#    print data
#   Finding out the maximum reachable handshake time corresponding to 10 Gbps data rate and different BER values
#    DR=10e9
#    AvgHSTime=10
#    BER = 1*1e-3
#    HandshakeList=[]
#    Values=[]
#    x=1
#    while(x<10):
#        HSTime=Handshake(flights,HandshakeList,RetransmissionCriteria='exponential',LossRate=BER, datarate = DR)
#        if(HSTime):
#            Values.append(HSTime)
#            x=x+1
#            print 'successful handshakes ', len(Values)
#    AvgHSTime=np.mean(Values)
#    print 'Average ==',AvgHSTime
        


#    HandshakeList=[]
#        LossRate=0, datarate =32000000)
#    print HandshakeList




#    Plotted (2D) Datarate vs HSTime in order to find the lowest possible datarate
#    for a successful handshake

#    HStimes=[]
#    Datarates=[]
#    drate=1000
#    while (drate<2e5):
#        hs = Handshake(flights,HandshakeList,RetransmissionCriteria='exponential', \
#        LossRate=3e-3, datarate=drate)
#        if(hs!=None):
#            Datarates.append(drate)
#            HStimes.append(hs)
#            print "Drate : ", drate, " -- HS : ", hs, "\n" 
#        drate=drate+50000
#    plt.figure()
#    plt.xlabel("Data Rate")
#    plt.ylabel("HS")
#    plt.plot( Datarates, HStimes,"r")
#    plt.show()
       

#    print HandshakeList

#    print '------------ low Range ------------ \n'
#    HStime_BER_DR_HeatMap_Data(flights, 1000,1e4, 1e6, 1e4, 1e-7, 5e-4)
#    print '_________________________________________________________________________________________________________________ \n'
#    print '------------ high Range ------------ \n'
#    HStime_BER_DR_HeatMap_Data(flights, 1000,1e6, 50e6, 1e6, 1e-7, 5e-4)

#-----------------------------------------------------------------------------------------------------------------------------
# .......................................... CHAPTER 2 .......................................................................
   

#   the number of retransmissions per handshake per BER for a data rate of 1 Mbps
#    plot_BER_vs_TotalRetransmission(1e-7, 1e-3, 100.0, 1e6, flights3)


#   Finding the relation between the BER and the average number of retransmissions per flight
#    plot_BER_vs_TotalRetransmission_per_Flight(1e-7, 1e-3, 10000.0, 1e6, flights3)


#    number of retransmissions per message
#    plot_BER_vs_superfluousData(1e-7, 1e-3, 10000.0, 1e6, flights3) 


#    print '------------ low Range ------------ \n'
#    HStime_BER_DR_HeatMap_Data(flights3, 1000,1e4, 1e6, 1e4, 1e-7, 5e-4)
#    print '_________________________________________________________________________________________________________________ \n'
#    print '------------ high Range ------------ \n'
#    HStime_BER_DR_HeatMap_Data(flights3, 1000,1e6, 50e6, 1e6, 1e-7, 5e-4)




#.............................................................................................................................

##amrut

#    plot_BER_vs_superfluousData_per_HS(1e-7, 1e-3, 1000.0, 1e6, flights, flights_msg_size)
    
#    plot_BER_vs_superfluousData_per_HS(1e-7, 1e-3, 1000.0, 1e6, flights3, flights3_msg_size)
####################################################################################################################################

#    res=ackversion(flights,2)
#    for i in res:
#        print '#'
#        for e in i:
#            print str(e)


#    MultipleHandshakes(flights,1000,HandshakeList,'exponential',LossRate=0)

#    print HandshakeList
#    plotHistografm(HandshakeList)
#    plot_Mean_Variance_Median_Std_Against_LossRate(flights,1)

#    Handshake(ackversion(flights,1),HandshakeList)
#    plot_All_Handshakes('exponential',0,flights,ackversion(flights,1),ackversion(flights,2))

#    calculationsForPlots(flights,'linear')
#
# _____________________________________________________________________________
#
if __name__ == "__main__":
    main(sys.argv[1:]);


    
# ClientHello       --->
#                   <--- ServerHello
# ACK               --->
#                   <--- Certificate
# ACK               --->
#                   <--- ServerKeyExchange
# ACK               --->
#                   <--- CertificateRequest
# ACK               --->
#                   <--- ServerHelloDone
# Certificate       --->
#                   <--- ACK
# ClientKeyExchange --->
#                   <--- ACK
# CertificateVerify --->
#                   <--- ACK
# ChangeCipherSpec  --->
#                   <--- ACK
# Finished          --->
#                   <--- ChangeCipherSpec
# ACK               --->
#                   <--- Finished

    
# ClientHello       --->
#                   <--- ServerHello
#                   <--- Certificate
#                   <--- ServerKeyExchange
#                   <--- CertificateRequest
#                   <--- ServerHelloDone
# Certificate       --->
# ClientKeyExchange --->
# CertificateVerify --->
# ChangeCipherSpec  --->
# Finished          --->
#                   <--- ChangeCipherSpec
#                   <--- Finished
# ACK               --->



