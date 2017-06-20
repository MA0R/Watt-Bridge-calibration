"""
A general instrument class, that provides wrappers for commands and returns
a status for the command or query. To be used in conjunction with the 'com'
function in the data collection threads.It can be used as a base class
and further more specialised functions can be added, like a 'reset' function
for a specific instrument.
"""

import time
class INSTRUMENT(object):
    def __init__(self,inst_bus, **kwargs):
        self.com = {'label':'', 'Ranges':[], 'measure_seperation':'0', 'NoError':'','reset':'','status':'','init':'','MakeSafe':'', 'error':'', 'SettleTime':'0', 'SetValue':'$', 'MeasureSetup':'','SingleMsmntSetup':''} #command dictionary
        self.com.update(kwargs) #update dictionary to include all sent commands.
        self.label = self.com["label"]
        self.bus = self.com['bus']
        #ensure values are ints
        try:
            self.com_settle_time = float(self.com['SettleTime'])
        except:
            print("settle time made into 1, from unreadable: "+str(self.com['SettleTime']))
            self.com_settle_time = 1
        try:
            self.measure_seperation = float(self.com['measure_seperation'])
        except:
            print("measure seperation made into 0, from unreadable: "+str(self.com['measure_seperation']))
            self.measure_seperation = 0

        self.inst_bus = inst_bus #save the instrument bus, either visa or the simulated visa
        

    def create_instrument(self):
        print("creating instruments")
        sucess = False
        string = string = str(time.strftime("%Y.%m.%d.%H.%M.%S, ", time.localtime()))+' Creating '+self.label+': '
        try:
            self.rm = self.inst_bus.ResourceManager()
            self.inst = self.rm.open_resource(self.bus)
            string = string+"sucess"
            sucess = True
        except self.inst_bus.VisaIOError:
            string = string+"visa failed"
            
        return [sucess,None,string]
    
    def send(self,command):
        sucess = False #did we read sucessfully
        #string to be printed and saved in log file
        string = str(time.strftime("%Y.%m.%d.%H.%M.%S, ", time.localtime()))+' writing to '+self.label+': '
        string = string+str(command)
        try:
            self.inst.write(command)
            time.sleep(self.com_settle_time)
            string = string+", success "
            sucess = True
        except self.inst_bus.VisaIOError:
            string = string+", Visa failed"
        return [sucess,None,string]
    
    def read(self):
        val = '0' #value to be returned, string-type like instruments
        sucess = False #did we read sucessfully
        #string to be printed and saved in log file
        string = str(time.strftime("%Y.%m.%d.%H.%M.%S, ", time.localtime()))+' reading '+self.label+': ' 
        try:
            time.sleep(self.measure_seperation)
            val = self.inst.read()
            string = string+str(val)
            sucess = True
        except self.inst_bus.VisaIOError:
            sucess = True #TO BE REMOVED LATER
            string = string+"visa failed"
        return [sucess,val,string]
        
    def set_value(self, value):
        line = str(self.com['SetValue'])
        line = line.replace("$",str(value))
        return self.send(line)

