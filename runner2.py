#!/usr/bin/env python
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2009-2020 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    runner.py
# @author  Lena Kalleske
# @author  Daniel Krajzewicz
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @date    2009-03-26

from __future__ import absolute_import
from __future__ import print_function
import xml.etree.ElementTree as ET

import os
import sys
import optparse
import random

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa


def generate_routefile():
    random.seed(42)  # make tests reproducible
    N = 2000  # number of time steps
    # demand per second from different directions
    pWE = 1. / 10
    pEW = 1. / 12
    pNS = 1. / 50
    with open("data/cross.rou.xml", "w") as routes:
        print("""<routes>
        <vType id="typeWE" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" \
guiShape="passenger"/>
        <vType id="typeNS" accel="0.8" decel="4.5" sigma="0.5" length="7" minGap="3" maxSpeed="25" guiShape="bus"/>

        <route id="right" edges="51o 1i 2o 52i" />
        <route id="left" edges="52o 2i 1o 51i" />
        <route id="down" edges="54o 4i 3o 53i" />""", file=routes)
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
        print("</routes>", file=routes)

# The program looks like this
#    <tlLogic id="0" type="static" programID="0" offset="0">
# the locations of the tls are      NESW
#        <phase duration="31" state="GrGr"/>
#        <phase duration="6"  state="yryr"/>
#        <phase duration="31" state="rGrG"/>
#        <phase duration="6"  state="ryry"/>
#    </tlLogic>
import traci.constants as tc
first = False
def run():
    """execute the TraCI control loop"""
    step = 0
    # we start with phase 2 where EW has green
    #traci.trafficlight.setPhase("0", 0)
    #print(traci.junction.getIDList())
    #print(traci.trafficlight.getAllProgramLogics('0'))
    test = 0
    s = 0
    '''
    network = ET.parse('data/cross.net.xml')
    signal = network.find('tlLogic') 
    dur = [34,6,31,6] 
    i = 0
    global first
    
    for phase in signal.iter('phase'):
        #print('phase')
        if first:
            phase.set("duration", str(dur[i]))
        else:
            phase.set("duration", str(int(particle.pos[i])))
        i+=1
        first = False
    '''

    #network.write("data/cross.net.xml")
    print(traci.trafficlight.getIDList())
    for idl in traci.trafficlight.getIDList():
        print(traci.trafficlight.getRedYellowGreenState(idl))
        print(int((len(traci.trafficlight.getRedYellowGreenState(idl)) ** 0.5) * 2))
    #print(traci.trafficlight.getCompleteRedYellowGreenDefinition('0')[0].getPhases()[0])
    print([traci.trafficlight.getAllProgramLogics(i)[0].phases[0].state \
        for i in traci.trafficlight.getIDList()])
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        test+= 1
        #print(traci.vehicle.getAccumulatedWaitingTime)
        for v in traci.vehicle.getIDList():
            s+=traci.vehicle.getWaitingTime(v)
            #traci.simulation.del
       
        step += 1
        if step >=1000:
            break
    print(s)    
    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options

# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # first, generate the route file for this simulation
    #generate_routefile()

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    traci.start(['sumo-gui', "-c", "data2/cross.sumocfg",
                             "--tripinfo-output", "data2/tripinfo.xml"])
    #vehID = traci.vehicle.getIDList()[0]
    #traci.vehicle.subscribe(vehID, (tc.VAR_ROAD_ID, tc.VAR_LANEPOSITION))
    #print(print(traci.vehicle.getSubscriptionResults(vehID)))
    run()
    