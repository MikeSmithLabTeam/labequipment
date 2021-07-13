import numpy as np
import matplotlib.pyplot as plt
from PyDAQmx import *
from ctypes import *
import time as t

'''Data acquisition classes for year 2 lab, School of Physics and Astronomy, University of Nottingham
for National Instruments DAQ PCI6221.
This makes use of the PyDAQmx package to interface to the NIDAQmx ANSI C driver.
For more information on PyDAQmx: https://pythonhosted.org/PyDAQmx/
NIDAQmx C Reference help: http://zone.ni.com/reference/en-XX/help/370471AM-01/
Also includes simulation modules for Peltier and dielectrics experiments'''

class digital:
    def __init__(self, reset=True):
        if reset:
            DAQmxResetDevice('Dev1')
        self.tDO = Task()
        self.tDO.CreateDOChan('Dev1/port0/line0:7','',DAQmx_Val_ChanForAllLines)
        self.do = np.array([0]*8,np.uint8)
        self.tDO.StartTask()
        
    def __end__(self):
        self.tDO.StopTask()
        self.tDO.ClearTask()
        
    def write(self, what):
        self.do = what
        self.tDO.WriteDigitalLines(1,1,10.0,DAQmx_Val_GroupByChannel,self.do,None,None);
        
    def clear(self):
        self.do = np.array([0]*8,np.uint8)
        self.tDO.WriteDigitalLines(1,1,10.0,DAQmx_Val_GroupByChannel,self.do,None,None);


class analog:
    def __init__(self, reset=True):
        if reset:
            DAQmxResetDevice('Dev1')       
        self.tAI = Task()
        self.tAO = Task()
        self.Nscans = 1000
        self.Rate = 1000
        self.Range = [10,10,10,10,10,10,10,10]
        self.__chans = [0,0,0,0,0,0,0,0]
        self.__Nch = 0
        self.__outchans = [0,0]
        self.__Noutch = 0
        
    def addOutput(self,Chan,Range=10):
    #initialize analog output channel
        if Chan == 0:
            self.tAO.CreateAOVoltageChan("Dev1/ao0","",-Range,Range,DAQmx_Val_Volts,None)
            self.__outchans[0]=1
            self.__outchans[1]=0
        elif Chan == 1:
            self.tAO.CreateAOVoltageChan("Dev1/ao1","",-Range,Range,DAQmx_Val_Volts,None)
            self.__outchans[1]=1
            self.__outchans[0]=0
        else:
            print('no such channel')
        self.__Noutch = sum(self.__outchans)
        
    def write(self,data,continuous=False):
    #dc or ac output
        if self.__Noutch == 0:
            print('no analog output channels configured')
        elif self.__Noutch == 1:
            if isinstance(data,(int,float)):
                self.tAO.WriteAnalogScalarF64(1,0,data,None)
            elif isinstance(data,(np.ndarray)):
            # set sampling parameters e.g. rate and duration
               # if data.size == 1:
               #     self.tAO.WriteAnalogScalarF64(1,0,data,None)
               # else:
                rate=np.int(self.Rate)
                maxRate = 833000
                if rate > maxRate:
                    rate = maxRate
                    print('Rate set to',rate,'(upper limit)')
                if continuous:
                    self.tAO.CfgSampClkTiming(None,rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,data.size)
                    sampsperchanwritten=int32()
                    # write the data to the DAQ card and set auto trigger to false so that we can start it with Start Task
                    self.tAO.WriteAnalogF64(data.size,False,10,DAQmx_Val_GroupByChannel,data,byref(sampsperchanwritten),None)
                    self.tAO.StartTask()
                else:                        
                    timeout=data.size/self.aoRate + 5
                    self.tAO.CfgSampClkTiming(None,rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,data.size)
                    sampsperchanwritten=int32()
                    # write the data to the DAQ card and set auto trigger to false so that we can start it with Start Task
                    self.tAO.WriteAnalogF64(data.size,False,timeout,DAQmx_Val_GroupByChannel,data,byref(sampsperchanwritten),None)
                    self.tAO.StartTask()
                    self.tAO.WaitUntilTaskDone(timeout)
                    self.tAO.StopTask()
                    return sampsperchanwritten
            else:
                print('argument should be a float or a numpy array')
    
    def writeSingle(self,value):
    #output DC voltage
        if self.__Noutch == 0:
            print('no analog output channels configured')
        else:
            self.tAO.WriteAnalogScalarF64(1,0,value,None)
    
    def writeContinuous(self,data):
    #continuous waveform output
        if self.__Noutch == 0:
            print('no analog output channels configured')
        else:
            # set sampling parameters e.g. rate and duration 
            self.Rate=np.int(self.Rate)
            self.tAO.CfgSampClkTiming(None,self.aoRate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,data.size)
            sampsperchanwritten=int32()
            # write the data to the DAQ card and set auto trigger to false so that we can start it with Start Task
            self.tAO.WriteAnalogF64(data.size,False,10,DAQmx_Val_GroupByChannel,data,byref(sampsperchanwritten),None)
            self.tAO.StartTask()
    
    def stop(self):
    #stop output
        self.tAO.StopTask()
    
    def addInput(self,Chan,Label="",Range=10):
    #initialize analog input channel with input range +/-Range
        if Chan == 0:
            self.tAI.CreateAIVoltageChan("Dev1/ai0",Label,DAQmx_Val_Cfg_Default,-Range,Range,DAQmx_Val_Volts,None)
            self.__chans[0] = 1
        elif Chan == 1:
            self.tAI.CreateAIVoltageChan("Dev1/ai1",Label,DAQmx_Val_Cfg_Default,-Range,Range,DAQmx_Val_Volts,None) 
            self.__chans[1] = 1
        elif Chan == 2:
            self.tAI.CreateAIVoltageChan("Dev1/ai2",Label,DAQmx_Val_Cfg_Default,-Range,Range,DAQmx_Val_Volts,None)
            self.__chans[2] = 1
        elif Chan == 3:
            self.tAI.CreateAIVoltageChan("Dev1/ai3",Label,DAQmx_Val_Cfg_Default,-Range,Range,DAQmx_Val_Volts,None) 
            self.__chans[3] = 1
        elif Chan == 4:
            self.tAI.CreateAIVoltageChan("Dev1/ai4",Label,DAQmx_Val_RSE,-Range,Range,DAQmx_Val_Volts,None) 
            self.__chans[4] = 1
        elif Chan == 5:
            self.tAI.CreateAIVoltageChan("Dev1/ai5",Label,DAQmx_Val_RSE,-Range,Range,DAQmx_Val_Volts,None) 
            self.__chans[5] = 1  
        elif Chan == 6:
            self.tAI.CreateAIVoltageChan("Dev1/ai6",Label,DAQmx_Val_RSE,-Range,Range,DAQmx_Val_Volts,None) 
            self.__chans[6] = 1
        elif Chan == 7:
            self.tAI.CreateAIVoltageChan("Dev1/ai7",Label,DAQmx_Val_RSE,-Range,Range,DAQmx_Val_Volts,None) 
            self.__chans[7] = 1
        else:
            print('no such channel')
        self.__Nch = sum(self.__chans)
       # if self.__Nch > 0:
       #     maxRate = np.int(250000/self.__Nch)
       #     if self.Rate > maxRate:
       #         self.Rate = maxRate
       #         print('sampling rate set to',self.Rate,'Hz (upper limit)')
    
    def addTrigger(self,pretriggersamples=1000):
    #set up triggering off rising edge of digital signal on PFI0
    #(labeled 'ANTRIG' on breakout box)
        self.Nscans=np.int(self.Nscans)
        self.Rate=np.int(self.Rate)
        self.tAI.CfgSampClkTiming("",self.Rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,self.Nscans)
        self.tAI.CfgDigEdgeRefTrig('PFI0',DAQmx_Val_Rising,pretriggersamples)
    
    def read(self):
    #read Nscans date points on each configured input channel
        if self.__Nch == 0:
            print('no analog input channels configured')
        else:
            maxRate = 250000/self.__Nch
            if self.Rate > maxRate:
                self.Rate = maxRate
                print('sampling rate exceeds upper limit; set to',self.Rate,'Hz')
            self.Rate=np.int(self.Rate)
            self.Nscans=np.int(self.Nscans)
            data = np.zeros(self.__Nch*self.Nscans)
            read=int32()
            timeout=self.Nscans/self.Rate + 5
            # set sampling parameters e.g. rate and duration
            self.tAI.CfgSampClkTiming("",self.Rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,self.Nscans)
            # start the analog input (AI) task
            self.tAI.StartTask()
            # read the data from the DAQ card
            self.tAI.ReadAnalogF64(self.Nscans,timeout,DAQmx_Val_GroupByChannel,data,self.__Nch*self.Nscans,byref(read),None)
            # create a meaningful time axis using sampling parameters
            self.tAI.WaitUntilTaskDone(timeout)
            self.tAI.StopTask()
            timestamps=np.arange(self.Nscans)/self.Rate
            # rearrange data arrange if >1 input channel
            if self.__Nch > 1:
                data=data.reshape(self.__Nch,self.Nscans)        
            return data,timestamps
    
    def run(self,outdata):
    #run simultaneous analog input and output
    #input channel uses the output sample clock and must be started first
        if self.__Nch == 0:
            print('no analog input channels configured')
        elif self.__Noutch == 0:
            print('no analog output channels configured') 
        else:
            indata = np.zeros(self.__Nch*outdata.size)
            read=int32()
            sampsperchanwritten=int32()
            self.Rate = np.int(self.Rate)
            timeout=outdata.size/self.Rate + 5
        # set sampling parameters e.g. rate and duration
        #self.tAI.CfgSampClkTiming(None,self.aiRate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,outdata.size)
            self.tAO.CfgSampClkTiming(None,self.Rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,outdata.size)
            self.tAI.CfgSampClkTiming('ao/SampleClock',self.Rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,outdata.size)
        # write the data to the DAQ card and set auto trigger to false so that we can start it with Start Task
            self.tAO.WriteAnalogF64(outdata.size,False,0,DAQmx_Val_GroupByChannel,outdata,byref(sampsperchanwritten),None)
        # start the AO and AI tasks
            self.tAI.StartTask()
            self.tAO.StartTask()
        # read the data from the DAQ card
            self.tAI.ReadAnalogF64(outdata.size,timeout,DAQmx_Val_GroupByChannel,indata,self.__Nch*outdata.size,byref(read),None)
            self.tAI.StopTask()
            self.tAO.StopTask()
        # create a meaningful time axis using sampling parameters
            timestamps=np.arange(outdata.size)/self.Rate
        # rearrange data arrange if >1 input channel
            if self.__Nch > 1:
                indata.shape = (self.__Nch,outdata.size)        
            return indata,timestamps 
#    def setRange(self,chan,value):
#        #set the input Range on channel number chan to +/- value (in volts) 
#        self.Range[chan] = value
#        self.configAI(chan)
    
    def reset(self):
        #reset the device
        DAQmxResetDevice('Dev1')
        self.__chans=[0,0,0,0,0,0,0,0]
        self.__Nch = 0
        self.__outchans=[0,0]
        self.__Noutch = 0
        #self.Range = [10,10,10,10,10,10,10,10] 
    
    def clear(self):
        #clear the task
        self.tAI.DAQmxClearTask()
        self.tAO.DAQmxClearTask()
        
#example usage:
#import y2lab

#dio = y2lab.digital()
#dio.set(np.array([0,0,0,0,1,0,1,0],dtype=np.uint8))

#aio = daq.analog()
#aio.addInput(0)
#aio.Rate = 500
#aio.Nscans = 2000
#data,timestamps = aio.read()
        
#aio.addOutput(0)
#aio.write(1.0)
#aio.write(0.0)
#t=np.arange(1000)/500
#outdata=5*np.sin(2*np.pi*20*t, dtype=np.float64)
#aio.write(outdata)
#data,timestamps = aio.run(outdata)
        
