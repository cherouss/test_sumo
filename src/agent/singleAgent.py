
class agent():

	def __init__(self, ):
		self.createModel()

	'''
		create model for every traffic light
	'''
	
    def reward(self):
        vehicles =traci.vehicle.getIDList()
        for vhc in vehicles:
            waiting_time += traci.vehicle.getAccumulatedWaitingTime(vhc)
            carbon_omission += traci.vehicle.getCO2Emission(vhc)
        return waiting_time, carbon_omission

	def state(self, lane_id):
		for id in lane_id:
            queue = traci.lane_area.getLaststenvehicleNumber(id)
        return queue
	

	def getPreProcessData(self, totaldays):

		preData = {}
		for i in ni.trafficLights:
			preData[i] = []
		sumoCmd = ["sumo", "-c", ni.sumocfg, "--ignore-route-errors", "--time-to-teleport", "600"]
		for i in range(totaldays):
			self.log.debug('collecting preprocess data: ' + str(i) + ' days')
			getNewDemand()
			traci.start(sumoCmd)
			self.createRecord()
			step = 0
			while step < 7200:
				self.addRecord(step, addVehicleRecord = False)
				step += 1
				for tl in ni.trafficLights:
					flag = util.adjustFlag(tl, self.record)
					if flag:
						feature = util.getFeature(tl, self.record)
						preData[tl].append(feature)
				traci.simulationStep()
			traci.close()
			#self.clearRecord()
			if (i+1)%10 == 0:
				for tl in ni.trafficLights:
					a = np.array(preData[tl])
					a = np.array(a)
					file = 'preprocess/' +tl 
					np.save(file, a)
				#torch.save(preData, 'preprocess.pt')

	def train(self, totaldays):

		self.loadScaler()
		
		savedays = 4
		starttraindays = 3 
		sumoCmd = ["sumo", "-c", ni.sumocfg, "--ignore-route-errors", "--time-to-teleport", "600"]
		for i in range(totaldays):
			
			getNewDemand()
			self.createRecord()
			self.log.debug('train ' + str(i) + ' epoch')

			traci.start(sumoCmd)
			step = 0
			while step < 7200:
				self.simulation(traci, step)
				step += 1
				if i >= starttraindays:
					for tl in ni.trafficLights:
						self.model[tl].train(tl ,self.log)
			traci.close()
			if (i+1)%savedays == 0:
				savefile = 'model/'+'version'+str(int((i+1)/savedays)) + '_'
				self.log.debug('save model, reward and step in ' + savefile)
				for tl in ni.trafficLights:
					file = savefile + tl
					self.model[tl].save(file)

	def clearRecord(self):
		self.createRecord()

	def simulation(self, traci, step):
		self.addRecord(step)
		for tl in ni.trafficLights:
			self.adjustTrafficLight(traci, tl)
		traci.simulationStep()

	def act(self, traci, action, tl):
        if action == 0 and phase == 1:
            traci.trafficlight.setPhaseDuration(tl,50)
        elif action == 1 :
            traci.trafficlight.setPhase(tl,0)

	

	def addexperience(self, tl):
		if len(self.record['state'][tl]) > 1:
			current = self.record['state'][tl][-1]
			last = self.record['state'][tl][-2]
			laststep = last[3]
			self.model[tl].append([last[0], last[1], current[0], last[2], current[4], laststep])

	def loadScaler(self):
		self.scaler = {}
		for tl in ni.trafficLights:
			file = 'preprocess/'+tl+'.npy'
			data = np.load(file)
			print(np.shape(data))
			self.log.debug('loading pre process scaler : '+ file)
			self.scaler[tl] = prep.StandardScaler().fit(data)

	