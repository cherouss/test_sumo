from itertools import cycle
import os
import sys
import random
import traci
import traci.constants as tc
from sumolib import checkBinary  
import numpy as np


#from __future__ import absolute_import
#from __future__ import print_function


import xml.etree.ElementTree as ET


from sumolib import checkBinary  # noqa
import traci  # noqa


def generate_routefile():
    random.seed(42)  # make tests reproducible
    N = 3600  # number of time steps
    # demand per second from different directions
    pWE = 1. / 20
    pEW = 1. / 22
    pNS = 1. / 40
    pSN = 1. / 38
    with open("data/new/cross.rou.xml", "w") as routes:
        print("""<routes>
        <vType id="typeWE" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" \
guiShape="passenger"/>
        <vType id="typeNS" accel="0.8" decel="4.5" sigma="0.5" length="7" minGap="3" maxSpeed="25" guiShape="bus"/>

        <route id="right" edges="51o 1i 2o 52i" />
        <route id="left" edges="52o 2i 1o 51i" />
        <route id="down" edges="54o 4i 3o 53i" />
        <route id="up" edges="53o 3i 4o 54i" />""", file=routes)
        vehNr = 0
        for i in range(N):
            if random.uniform(0, 1) < pWE:
                print('    <vehicle id="right_%i" type="typeWE" route="right" depart="%i" />' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pNS:
                print('    <vehicle id="down_%i" type="typeNS" route="down" depart="%i" color="1,0,0"/>' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pEW:
                print('    <vehicle id="left_%i" type="typeWE" route="left" depart="%i" />' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pSN:
                print('    <vehicle id="up_%i" type="typeNS" route="up" depart="%i" color="1,0,0"/>' % (
                    vehNr, i), file=routes)
                vehNr += 1
        print("</routes>", file=routes)



# this is the main entry point of this script




# this is the main entry point of this script

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
#generate_routefile()
class Agent():
    def __init__(self,act_dim,state_dim):
        self.phases = cycle([0,1,2,3,4,5,6,7])
        self.act_dim = act_dim
        self.his = []
        self.state_dim = state_dim
        self.terminate = False
        self.waiting_time = 0
        self.sim_step = 0
        self.current_phase_duration = 10
        #self.intersection_id 
        
        
        self.traci = traci
        self.intersection_id  =  None
        self.CO2_emission = 0
        #generate_routefile()
        self.state = (0,0,0,0,0,0,0,0,0)
        '''
        label = 0
        done = False
        while not done:
            try:
                self.traci.start(['sumo', "-c", "data/new/cross.sumocfg", '--waiting-time-memory', "4500", '--no-step-log', 'true', '-W', 'true' 
                ],label=str(label))
                done = True
            except:
                label+=1
        '''

    def reset(self):
        """
        try:
            traci.close()
            sys.stdout.flush()
        except:
            pass
        """
        generate_routefile()
        label = 0
        done = False
        self.waiting_time = 0
        while not done:
            try:
                self.traci.start(['sumo', "-c", "data/5edgesintersection/osm.sumocfg", '--waiting-time-memory',
                                  "4500", '--no-step-log', 'true', '-W', 'true'],label=str(label))
                done = True
            except:
                label+=1
        self.traci.simulationStep(10)
        self.sim_step +=10
        self.intersection_id= self.traci.trafficlight.getIDList()[0]
        self.CO2_emission = 0
    def get_reward(self):
        waiting_ = 0
        co2_emission = 0
        
        vehicles =self.traci.vehicle.getIDList()
        count = self.traci.vehicle.getIDCount()
        for vhc in vehicles:
            waiting_ += self.traci.vehicle.getAccumulatedWaitingTime(vhc)
            co2_emission = self.traci.vehicle.getCO2Emission(vhc)
            self.CO2_emission += co2_emission
        #reward = .75*waiting_ + .25 * co2_emission
        if count :
            return -(waiting_)/count
        return
    
    
    def step(self):
        #for i in range(step):
        curr = self.traci.simulation.getCurrentTime()
        #print(curr)
        self.traci.simulationStep(self.sim_step + 5)
        self.sim_step +=5
        self.current_phase_duration +=5
        #print(self.sim_step,curr)
        #test+= 1
        #print(traci.vehicle.getAccumulatedWaitingTime)
        for v in self.traci.vehicle.getIDList():
            self.waiting_time+=self.traci.vehicle.getWaitingTime(v)
            #traci.simulation.d
        if self.sim_step >3600 or self.traci.simulation.getMinExpectedNumber() == 0:
            #print('yoooooooooo')
            #print('here')
            self.terminate = True
            self.sim_step = 0
            self.current_phase_duration = 0
        if self.terminate:
            print(self.waiting_time)
            self.his.append([self.waiting_time,self.CO2_emission])
            traci.close()
            sys.stdout.flush()
            self.reset()
        #return self.get_state()
    def get_waiting_time(self):
        return self.waiting_time
    def get_state(self):
        t = self.traci.lanearea.getIDList()
        phase = self.traci.trafficlight.getPhase(self.intersection_id)
        lst = [int(phase),self.current_phase_duration]
        edge1 = [0]
        edge2 = [0,]
        x = 0 
        for i in t:
            #print(i)
            lst.append(traci.lanearea.getLastStepHaltingNumber(i))
            """
            if i == 'e2det_1i_0' or i == 'e2det_2i_0':
                #edge1[0] += traci.lanearea.getLastStepVehicleNumber(i)
                edge1[0] += traci.lanearea.getLastStepHaltingNumber(i)
                #edge1[1] += traci.lanearea.getLastStepMeanSpeed(i)
                #edge1[3] += traci.lanearea.getJamLengthVehicle(i)
                #nbr, speed = ,self.traci.lanearea.getLastStepMeanSpeed(i)
            else:
                #edge2[0] += traci.lanearea.getLastStepVehicleNumber(i)
                edge2[0] += traci.lanearea.getLastStepHaltingNumber(i)
                #edge2[1] += traci.lanearea.getLastStepMeanSpeed(i)
                #edge2[3] += traci.lanearea.getJamLengthVehicle(i)
            """
            #print(nbr, speed)
            #lst += nbr,speed
            x+=1
            #print(f'nbr of vehicles {traci.lanearea.getLastStepVehicleNumber(i)}')
            #print(f'mean speed {traci.lanearea.getLastStepMeanSpeed(i)}')
        return np.array(lst)
    def action(self,act):
        #if act == 0:
        #    print('errroooooor')
        phase = self.traci.trafficlight.getPhase(self.intersection_id)
        #print(phase)
        if act:
            #self.traci.simulationStep(self.sim_step + 5)
            #self.sim_step +=5
            self.traci.trafficlight.setPhaseDuration(self.intersection_id,5)
        else :
            if int(phase)%2 != 0 :
                
                self.traci.trafficlight.setPhase(self.intersection_id,next(self.phases))
                self.traci.simulationStep(self.sim_step + 3)
                self.sim_step +=3
                self.current_phase_duration = 3
                #self.traci.trafficlight.setPhaseDuration('0',5)
                #self.traci.trafficlight.setPhase('0',next(self.phases))
            else:
                #self.traci.simulationStep(self.sim_step + 5)
                #self.sim_step +=5
                self.traci.trafficlight.setPhase(self.intersection_id,next(self.phases))
                self.current_phase_duration = 0
        
        state = self.get_state()
        for i in range(len(state)):
            if np.isnan(state[i]):
                print('yessssssssssssss')
                print(state)
                state[i] =0
                print(state)
        
                
        reward = self.get_reward()
        #reward = np.clip(-100,100,self.get_reward())
        
        return state , reward , self.terminate
            
#a= Agent(2,8)