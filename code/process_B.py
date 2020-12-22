def main():
	import argparse

	parser = argparse.ArgumentParser()

	parser.add_argument('-cn')

	args = parser.parse_args()

	# --

	if args.cn:
		conf_name = args.cn

	else:
		with open('conf-name.json') as i_file:
			import json

			# --

			conf_name = json.loads(i_file.read())

	print(conf_name)
	
	# --
	
	with open(conf_name) as i_file:
		import json

		# --

		conf = json.loads(i_file.read())

	# --

	output = conf['inter-output']

	# --

	from module.RDF import RDF

	RDF = RDF()

	# --

	print('load example generator')

	E_G = Example_Generator(conf)

	# --

	print('generate positive example')

	P = E_G.generate_P()

	# --

	with open(output + '/P.tsv', 'w+') as o_file:
		for p in sorted(P):
			for s, o in sorted(P[p]):
				o_file.write('\t'.join([s, p, o]) + '\n')

	with open(output + '/P-simple.tsv', 'w+') as o_file:
		for p in sorted(P):
			for s, o in sorted(P[p]):
				o_file.write('\t'.join([RDF.remove_prefix(s), RDF.remove_prefix(p), RDF.remove_prefix(o)]) + '\n')

	# --

	print('generate negative example')

	N = E_G.generate_N()

	# --

	with open(output + '/N.tsv', 'w+') as o_file:
		for p in sorted(N):
			for s, o in sorted(N[p]):
				o_file.write('\t'.join([s, p, o]) + '\n')

	with open(output + '/N-simple.tsv', 'w+') as o_file:
		for p in sorted(N):
			for s, o in sorted(N[p]):
				o_file.write('\t'.join([RDF.remove_prefix(s), RDF.remove_prefix(p), RDF.remove_prefix(o)]) + '\n')

	# --

	print('positive property', len(P))
	print('negative property', len(N))

	# --

	P_num = 0

	for p in P:
		P_num += len(P[p])

	N_num = 0

	for p in N:
		N_num += len(N[p])

	print('positive example', P_num)
	print('negative example', N_num)

# --

class Example_Generator:
	FW = 1
	BW = -1

	# --

	def __init__(self, conf):
		output = conf['inter-output']

		# --

		class_parent_path = conf['class-parent-path']
		
		type_path = conf['type-path']
		inst_path = conf['inst-path-A']

		# --

		use_OT = conf['use-OT']
		self.use_MST = conf['use-MST']

		self.use_CWA = conf['use-LCWA']
		self.use_LCWA = conf['use-ELCWA']
		self.use_DLCWA = conf['use-DLCWA']

		self.use_S = conf['use-S']
		self.use_F = conf['use-F']
		self.s_threshold = conf['s-threshold']

		p_path = conf['p-path']
		self.e_size = conf['e-size']
		self.n_rate = conf['n-rate']
		self.m_size = conf['m-size']

		self.max_distance = conf['max-distance-A']

		self.process_num = conf['process-num']

		# --

		from module.TSV import TSV

		TSV = TSV()

		from module.RDF import RDF

		self.RDF = RDF()

		# --

		self.class_parent = TSV.read_dict(class_parent_path, func=True)

		# --

		is_class = {}

		for c in self.class_parent:
			is_class[c] = True

			# --

			is_class[self.class_parent[c]] = True

		# -- 타입

		type_list = []

		for path in type_path:
			type_list.append(TSV.read_dict(path))

		self.type_ = self.merge_type(type_list)

		# -- 타입 정제

		if use_OT:
			for e in dict(self.type_):
				for t in set(self.type_[e]):
					# 근거: 온톨로지 타입 계층 상의 클래스만을 작업의 범위로 한정
					try:
						is_class[t]

					except:
						self.type_[e].remove(t)

				# --

				if len(self.type_[e]) <= 0:
					del self.type_[e]

		# -- 인스턴스

		inst_list = []

		for path in inst_path:
			inst_list.append(TSV.read_list(path))

		inst = self.merge_inst(inst_list)

		# -- S

		if self.use_S:
			self.S = {}

			# --

			for p1, d1, p2, d2, s in TSV.read_list(output + '/S.tsv'):
				self.S[p1, int(d1), p2, int(d2)] = float(s)

		# -- F

		if self.use_F:
			self.F = {}

			# --

			for p, d, f in TSV.read_list(output + '/F.tsv'):
				self.F[p, int(d)] = float(f)

		# -- preparation

		p2so = {}
		self.so2p = {}

		self.s2p = {}
		self.o2p = {}

		self.t2e = {}
		self.e2t2e = {}
		self.p2t2s = {}
		self.p2t2o = {}

		self.is_positive = {}

		for s, p, o, ot in inst:
			if ot in ['object']:
				if s == o:
					continue

				# --
				
				try:
					p2so[p].add((s, o))

				except:
					p2so[p] = set([(s, o)])

				# --

				try:
					self.so2p[s, o].add(p)

				except:
					self.so2p[s, o] = set([p])

				# --

				try:
					self.s2p[s].add(p)

				except:
					self.s2p[s] = set([p])

				# --

				try:
					self.o2p[o].add(p)

				except:
					self.o2p[o] = set([p])

				# --

				try:
					for t in self.type_[o]:
						try:
							self.t2e[t].add(o)

						except:
							self.t2e[t] = set([o])

						# --

						try:
							self.e2t2e[s]

						except:
							self.e2t2e[s] = {}

						try:
							self.e2t2e[s][t].add(o)

						except:
							self.e2t2e[s][t] = set([o])

						# --

						try:
							self.p2t2o[p]

						except:
							self.p2t2o[p] = {}

						try:
							self.p2t2o[p][t].add(o)

						except:
							self.p2t2o[p][t] = set([o])

				except:
					pass

				# --

				try:
					for t in self.type_[s]:
						try:
							self.t2e[t].add(s)

						except:
							self.t2e[t] = set([s])
							
						# --

						try:
							self.e2t2e[o]

						except:
							self.e2t2e[o] = {}

						try:
							self.e2t2e[o][t].add(s)

						except:
							self.e2t2e[o][t] = set([s])

						# --

						try:
							self.p2t2s[p]

						except:
							self.p2t2s[p] = {}

						try:
							self.p2t2s[p][t].add(s)

						except:
							self.p2t2s[p][t] = set([s])

				except:
					pass

				# --

				self.is_positive[s, p, o] = True

		# --

		self.p_list = []

		if p_path:
			for path in p_path:
				with open(path) as i_file:
					import json

					# --

					self.p_list += json.loads(i_file.read())

			# --

			self.p_list = sorted(set(self.p_list) & p2so.keys())
			
		else:
			self.p_list = sorted(p2so.keys())

		# --

		pa2pb = {}
		pp2so = {}

		for pa in self.p_list:
			for s, o in p2so[pa]:
				for pb in self.s2p[s]:
					try:
						pa2pb[pa].add((pb, 'S-FW'))

					except:
						pa2pb[pa] = set([(pb, 'S-FW')])

					# --

					try:
						pp2so[pa, pb, 'S-FW'].add((s, o))

					except:
						pp2so[pa, pb, 'S-FW'] = set([(s, o)])

				# --
				
				try:
					for pb in self.o2p[s]:
						try:
							pa2pb[pa].add((pb, 'S-BW'))

						except:
							pa2pb[pa] = set([(pb, 'S-BW')])

						# --

						try:
							pp2so[pa, pb, 'S-BW'].add((s, o))

						except:
							pp2so[pa, pb, 'S-BW'] = set([(s, o)])

				except:
					pass

				# --

				try:
					for pb in self.s2p[o]:
						try:
							pa2pb[pa].add((pb, 'O-FW'))

						except:
							pa2pb[pa] = set([(pb, 'O-FW')])

						# --

						try:
							pp2so[pa, pb, 'O-FW'].add((s, o))

						except:
							pp2so[pa, pb, 'O-FW'] = set([(s, o)])

				except:
					pass

				# --

				for pb in self.o2p[o]:
					try:
						pa2pb[pa].add((pb, 'O-BW'))

					except:
						pa2pb[pa] = set([(pb, 'O-BW')])

					# --

					try:
						pp2so[pa, pb, 'O-BW'].add((s, o))

					except:
						pp2so[pa, pb, 'O-BW'] = set([(s, o)])

		# --

		self.P = {}

		for p in self.p_list:
			self.P[p] = p2so[p]

		# --

		self.P_comp = {}

		for pa in self.p_list:
			self.P_comp[pa] = {}

			# --

			for pb, pb_type in pa2pb[pa]:
				self.P_comp[pa][pb, pb_type] = pp2so[pa, pb, pb_type]

		# -- cache for multi-processing

		self.cache = {}

		for p in self.p_list:
			self.cache['CWA', p, self.FW] = {}
			self.cache['CWA', p, self.BW] = {}
			self.cache['LCWA', p, self.FW] = {}
			self.cache['LCWA', p, self.BW] = {}
			self.cache['DLCWA', p, self.FW] = {}
			self.cache['DLCWA', p, self.BW] = {}

	# --

	def generate_P(self):
		P_samp = {}

		P_comp_samp = {}

		# --

		for pa in self.p_list:
			P_samp[pa] = set([])

			P_comp_samp[pa] = {}

			for pb, pb_type in self.P_comp[pa]:
				P_comp_samp[pa][pb, pb_type] = set([])

			# --

			E = set(self.sample_data(self.P[pa], self.e_size - len(P_samp[pa])))

			P_samp[pa] |= E

			self.compensate(E, P_comp_samp[pa], self.m_size)

			# --

			for pb, pb_type in self.P_comp[pa]:
				E = set(self.sample_data(self.P_comp[pa][pb, pb_type], self.m_size - len(P_comp_samp[pa][pb, pb_type])))

				P_comp_samp[pa][pb, pb_type] |= E

				self.compensate(E, P_comp_samp[pa], self.m_size)

		# --

		self.P_samp = dict(P_samp)

		self.P_comp_samp = dict(P_comp_samp)

		# --

		result = {}

		for pa in self.p_list:
			result[pa] = set(P_samp[pa])

			# --

			for pb, pb_type in P_comp_samp[pa]:
				result[pa] |= set(P_comp_samp[pa][pb, pb_type])

		# --

		return result

	# --

	def generate_N(self):
		N_samp = {}

		N_comp_samp = {}

		# --

		i = 1

		for pa in self.p_list:
			N_samp[pa] = set([])

			N_comp_samp[pa] = {}

			for pb, pb_type in self.P_comp[pa]:
				N_comp_samp[pa][pb, pb_type] = set([])

			# --

			P_shuffled = self.shuffle_data(self.P[pa])

			P_comp_shuffled = {}

			for pb, pb_type in self.P_comp[pa]:
				P_comp_shuffled[pb, pb_type] = self.shuffle_data(self.P_comp[pa][pb, pb_type])

			# --

			e_size = self.e_size * self.n_rate

			m_size = self.m_size * self.n_rate

			# -- generation direction

			if self.use_F:
				if self.F[pa, self.FW] >= self.F[pa, self.BW]:
					direction = [self.FW] # S 고정, O 치환

				else:
					direction = [self.BW] # S 치환, O 고정

			else:
				direction = [self.FW, self.BW]

			# -- CWA

			if self.use_CWA:
				for d in direction:
					N_samp[pa] |= self.NEG_CWA(P_shuffled, e_size - len(N_samp[pa]), pa, d)

					self.compensate(N_samp[pa], N_comp_samp[pa], m_size)

					print('CWA', self.RDF.remove_prefix(pa), '(%d / %d)' % (i, len(self.p_list)), len(P_shuffled), len(N_samp[pa]))

					# -- 보틀넥

					j = 0

					if len(N_samp[pa]) >= e_size:
						for pb, pb_type in P_comp_shuffled:
							if len(N_comp_samp[pa][pb, pb_type]) < m_size:
								N_comp_samp[pa][pb, pb_type] |= self.NEG_CWA(P_comp_shuffled[pb, pb_type], m_size - len(N_comp_samp[pa][pb, pb_type]), pa, d)

								self.compensate(N_comp_samp[pa][pb, pb_type], N_comp_samp[pa], m_size)

							# --

							print('CWA', self.RDF.remove_prefix(pa), '(%d / %d)' % (i, len(self.p_list)), self.RDF.remove_prefix(pb), '(%d / %d)' % (j, len(P_comp_shuffled)), len(P_comp_shuffled[pb, pb_type]), len(N_comp_samp[pa][pb, pb_type]))

							j += 1

			# -- LCWA

			if self.use_LCWA:
				for d in direction:
					N_samp[pa] |= self.NEG_LCWA(P_shuffled, e_size - len(N_samp[pa]), pa, d)

					self.compensate(N_samp[pa], N_comp_samp[pa], m_size)

					print('LCWA', self.RDF.remove_prefix(pa), '(%d / %d)' % (i, len(self.p_list)), len(P_shuffled), len(N_samp[pa]))

					# -- 보틀넥

					j = 0

					if len(N_samp[pa]) >= e_size:
						for pb, pb_type in P_comp_shuffled:
							if len(N_comp_samp[pa][pb, pb_type]) < m_size:
								N_comp_samp[pa][pb, pb_type] |= self.NEG_LCWA(P_comp_shuffled[pb, pb_type], m_size - len(N_comp_samp[pa][pb, pb_type]), pa, d)

								self.compensate(N_comp_samp[pa][pb, pb_type], N_comp_samp[pa], m_size)

							# --

							print('LCWA', self.RDF.remove_prefix(pa), '(%d / %d)' % (i, len(self.p_list)), self.RDF.remove_prefix(pb), '(%d / %d)' % (j, len(P_comp_shuffled)), len(P_comp_shuffled[pb, pb_type]), len(N_comp_samp[pa][pb, pb_type]))

							j += 1

			# -- DLCWA

			if self.use_DLCWA:
				for d in direction:
					N_samp[pa] |= self.NEG_DLCWA(P_shuffled, e_size - len(N_samp[pa]), pa, d)

					self.compensate(N_samp[pa], N_comp_samp[pa], m_size)

					print('DLCWA', self.RDF.remove_prefix(pa), '(%d / %d)' % (i, len(self.p_list)), len(P_shuffled), len(N_samp[pa]))

					# -- 보틀넥

					j = 0

					if len(N_samp[pa]) >= e_size:
						for pb, pb_type in P_comp_shuffled:
							if len(N_comp_samp[pa][pb, pb_type]) < m_size:
								N_comp_samp[pa][pb, pb_type] |= self.NEG_DLCWA(P_comp_shuffled[pb, pb_type], m_size - len(N_comp_samp[pa][pb, pb_type]), pa, d)

								self.compensate(N_comp_samp[pa][pb, pb_type], N_comp_samp[pa], m_size)

							# --

							print('DLCWA', self.RDF.remove_prefix(pa), '(%d / %d)' % (i, len(self.p_list)), self.RDF.remove_prefix(pb), '(%d / %d)' % (j, len(P_comp_shuffled)), len(P_comp_shuffled[pb, pb_type]), len(N_comp_samp[pa][pb, pb_type]))

							j += 1

			# --

			i += 1

		# --

		result = {}

		for pa in self.p_list:
			result[pa] = set(N_samp[pa])

			# --

			for pb, pb_type in N_comp_samp[pa]:
				result[pa] |= set(N_comp_samp[pa][pb, pb_type])

			# --

			if len(result[pa]) <= 0:
				del result[pa]

		# --

		return result

	# --

	def NEG_CWA(self, P, size, p, d):
		if size <= 0:
			N = set([])

			# --

			return N

		# --

		i_data = []

		# --

		o_data = []

		# --

		for s, o in P:
			try:
				for s_, o_ in self.cache['CWA', p, d][s, o]:
					o_data.append((s_, o_))

					# --

					if len(o_data) >= size:
						break
						
			except:
				i_data.append((s, o))

		# --

		if len(i_data) <= 0:
			N = set(list(set(o_data))[0:size])

			# --

			return N

		# --
		
		if len(o_data) >= size:
			N = set(list(set(o_data))[0:size])

			# --

			return N

		# --

		from multiprocessing import Manager, Process

		# --

		i_data_m = Manager().Queue()

		# --
		
		o_data_m = Manager().dict()

		# --

		for s, o in i_data:
			i_data_m.put((s, o), False)

		# --

		for s, o in o_data:
			o_data_m[s, o] = True
		
		# --

		cache = Manager().dict()

		# --

		pc_list = []

		# --

		if d in [self.FW]:
			for i in range(self.process_num):
				pc = Process(target=self.NEG_CWA_multi_A, args=(i_data_m, o_data_m, size, p, cache,))

				# --

				pc_list.append(pc)
				
		# --

		elif d in [self.BW]:
			for i in range(self.process_num):
				pc = Process(target=self.NEG_CWA_multi_B, args=(i_data_m, o_data_m, size, p, cache,))

				# --

				pc_list.append(pc)
		
		# --

		for pc in pc_list:
			pc.start()

		# --

		for pc in pc_list:
			pc.join()

		# --

		for pc in pc_list:
			pc.terminate()

		# --

		for pc in pc_list:
			del pc

		# --

		for s, o in cache.keys():
			try:
				self.cache['CWA', p, d][s, o] |= set(cache[s, o])

			except:
				self.cache['CWA', p, d][s, o] = set(cache[s, o])

		# --

		N = set(list(set(o_data_m.keys()))[0:size])

		# --

		return N

	# --

	def NEG_CWA_multi_A(self, i_data, o_data, size, p, cache):
		while True:
			try:
				s, o = i_data.get(False)

			except:
				break

			# -- 치환 후보 생성

			t_set = set([])

			try:
				if self.use_MST:
					t_set = self.get_mst(self.type_[o], self.class_parent)

				else:
					t_set = self.type_[o]

			except:
				cache[s, o] = set([])

				# --

				if len(o_data.keys()) >= size:
					break

				# --

				continue

			# --

			m_set = set([])

			for t in t_set:
				try:
					m_set |= self.t2e[t]

				except:
					pass

			# --

			exclusion = set([s, o])

			m_set = m_set - exclusion

			# -- 

			intersection = set([])

			for t in t_set:
				intersection |= self.p2t2o[p][t]

			m_set = m_set & intersection

			# -- 예제 생성

			gen_num = 0

			for m in self.shuffle_data(m_set):
				o_data[s, m] = True

				# --

				try:
					cache[s, o].add((s, m))

				except:
					cache[s, o] = set([(s, m)])

				# --

				gen_num += 1

				# --

				if gen_num >= self.n_rate:
					break

			# --

			if gen_num <= 0:
				cache[s, o] = set([])

			# --

			if len(o_data.keys()) >= size:
				break

	# --

	def NEG_CWA_multi_B(self, i_data, o_data, size, p, cache):
		while True:
			try:
				s, o = i_data.get(False)

			except:
				break

			# -- 치환 후보 생성

			t_set = set([])

			try:
				if self.use_MST:
					t_set = self.get_mst(self.type_[s], self.class_parent)

				else:
					t_set = self.type_[s]

			except:
				cache[s, o] = set([])

				# --

				if len(o_data.keys()) >= size:
					break

				# --

				continue

			# --

			m_set = set([])

			for t in t_set:
				try:
					m_set |= self.t2e[t]

				except:
					pass

			# --

			exclusion = set([s, o])

			m_set = m_set - exclusion

			# -- 

			intersection = set([])

			for t in t_set:
				intersection |= self.p2t2s[p][t]

			m_set = m_set & intersection

			# -- 예제 생성

			gen_num = 0

			for m in self.shuffle_data(m_set):
				o_data[m, o] = True

				# --

				try:
					cache[s, o].add((m, o))

				except:
					cache[s, o] = set([(m, o)])

				# --

				gen_num += 1

				# --

				if gen_num >= self.n_rate:
					break

			# --

			if gen_num <= 0:
				cache[s, o] = set([])

			# --

			if len(o_data.keys()) >= size:
				break

	# --

	def NEG_LCWA(self, P, size, p, d):
		if size <= 0:
			N = set([])

			# --

			return N

		# --

		i_data = []

		# --

		o_data = []

		# --

		for s, o in P:
			try:
				for s_, o_ in self.cache['LCWA', p, d][s, o]:
					o_data.append((s_, o_))

					# --

					if len(o_data) >= size:
						break
						
			except:
				i_data.append((s, o))

		# --

		if len(i_data) <= 0:
			N = set(list(set(o_data))[0:size])

			# --

			return N

		# --
		
		if len(o_data) >= size:
			N = set(list(set(o_data))[0:size])

			# --

			return N

		# --

		from multiprocessing import Manager, Process

		# --

		i_data_m = Manager().Queue()

		# --
		
		o_data_m = Manager().dict()

		# --

		for s, o in i_data:
			i_data_m.put((s, o), False)

		# --

		for s, o in o_data:
			o_data_m[s, o] = True
		
		# --

		cache = Manager().dict()

		# --

		pc_list = []

		# --

		if d in [self.FW]:
			for i in range(self.process_num):
				pc = Process(target=self.NEG_LCWA_multi_A, args=(i_data_m, o_data_m, size, p, cache,))

				# --

				pc_list.append(pc)
				
		# --

		elif d in [self.BW]:
			for i in range(self.process_num):
				pc = Process(target=self.NEG_LCWA_multi_B, args=(i_data_m, o_data_m, size, p, cache,))

				# --

				pc_list.append(pc)
		
		# --

		for pc in pc_list:
			pc.start()

		# --

		for pc in pc_list:
			pc.join()

		# --

		for pc in pc_list:
			pc.terminate()

		# --

		for pc in pc_list:
			del pc

		# --

		for s, o in cache.keys():
			try:
				self.cache['LCWA', p, d][s, o] |= set(cache[s, o])

			except:
				self.cache['LCWA', p, d][s, o] = set(cache[s, o])

		# --

		N = set(list(set(o_data_m.keys()))[0:size])

		# --

		return N

	# --

	def NEG_LCWA_multi_A(self, i_data, o_data, size, p, cache):
		while True:
			try:
				s, o = i_data.get(False)

			except:
				break

			# -- 치환 후보 생성

			t_set = set([])

			try:
				if self.use_MST:
					t_set = self.get_mst(self.type_[o], self.class_parent)

				else:
					t_set = self.type_[o]

			except:
				cache[s, o] = set([])

				# --

				if len(o_data.keys()) >= size:
					break

				# --

				continue

			# --

			n_set = set([])

			for t in t_set:
				try:
					n_set |= self.e2t2e[s][t]

				except:
					pass

			# --

			exclusion = set([s, o])

			n_set = n_set - exclusion

			# -- 

			intersection = set([])

			for t in t_set:
				intersection |= self.p2t2o[p][t]

			n_set = n_set & intersection

			# -- 예제 생성

			gen_num = 0

			for n in self.shuffle_data(n_set):
				c1 = True

				try:
					self.is_positive[s, p, n]

					c1 = False

				except:
					pass

				# --

				c2 = True

				if self.use_S:
					try:
						for p_n in self.so2p[s, n]:
							try:
								if self.S[p_n, self.FW, p, self.FW] > self.s_threshold:
									c2 = False

									break

							except:
								pass

					except:
						pass

					try:
						for p_n in self.so2p[n, s]:
							try:
								if self.S[p_n, self.BW, p, self.FW] > self.s_threshold:
									c2 = False

									break

							except:
								pass

					except:
						pass

				# --

				if c1 & c2:
					o_data[s, n] = True

					# --

					try:
						cache[s, o].add((s, n))

					except:
						cache[s, o] = set([(s, n)])

					# --

					gen_num += 1

					# --

					if gen_num >= self.n_rate:
						break

			# --

			if gen_num <= 0:
				cache[s, o] = set([])

			# --

			if len(o_data.keys()) >= size:
				break

	# --

	def NEG_LCWA_multi_B(self, i_data, o_data, size, p, cache):
		while True:
			try:
				s, o = i_data.get(False)

			except:
				break

			# -- 치환 후보 생성

			t_set = set([])

			try:
				if self.use_MST:
					t_set = self.get_mst(self.type_[s], self.class_parent)

				else:
					t_set = self.type_[s]

			except:
				cache[s, o] = set([])

				# --

				if len(o_data.keys()) >= size:
					break

				# --

				continue

			# --

			n_set = set([])

			for t in t_set:
				try:
					n_set |= self.e2t2e[o][t]

				except:
					pass

			# --

			exclusion = set([s, o])

			n_set = n_set - exclusion

			# --

			intersection = set([])

			for t in t_set:
				intersection |= self.p2t2s[p][t]

			n_set = n_set & intersection

			# -- 예제 생성

			gen_num = 0

			for n in self.shuffle_data(n_set):
				c1 = True

				try:
					self.is_positive[n, p, o]
					
					c1 = False

				except:
					pass

				# --

				c2 = True

				if self.use_S:
					try:
						for p_n in self.so2p[n, o]:
							try:
								if self.S[p_n, self.FW, p, self.FW] > self.s_threshold:
									c2 = False

									break

							except:
								pass

					except:
						pass

					try:
						for p_n in self.so2p[o, n]:
							try:
								if self.S[p_n, self.BW, p, self.FW] > self.s_threshold:
									c2 = False

									break

							except:
								pass

					except:
						pass

				# --

				if c1 & c2:
					o_data[n, o] = True

					# --

					try:
						cache[s, o].add((n, o))

					except:
						cache[s, o] = set([(n, o)])

					# --

					gen_num += 1

					# --

					if gen_num >= self.n_rate:
						break

			# --

			if gen_num <= 0:
				cache[s, o] = set([])

			# --

			if len(o_data.keys()) >= size:
				break

	# --

	def NEG_DLCWA(self, P, size, p, d):
		if size <= 0:
			N = set([])

			# --

			return N

		# --

		i_data = []

		# --

		o_data = []

		# --

		for s, o in P:
			try:
				for s_, o_ in self.cache['DLCWA', p, d][s, o]:
					o_data.append((s_, o_))

					# --

					if len(o_data) >= size:
						break
						
			except:
				i_data.append((s, o))

		# --

		if len(i_data) <= 0:
			N = set(list(set(o_data))[0:size])

			# --

			return N

		# --
		
		if len(o_data) >= size:
			N = set(list(set(o_data))[0:size])

			# --

			return N

		# --

		from multiprocessing import Manager, Process

		# --

		i_data_m = Manager().Queue()

		# --
		
		o_data_m = Manager().dict()

		# --

		for s, o in i_data:
			i_data_m.put((s, o), False)

		# --

		for s, o in o_data:
			o_data_m[s, o] = True
		
		# --

		cache = Manager().dict()

		# --

		pc_list = []

		# --

		if d in [self.FW]:
			for i in range(self.process_num):
				pc = Process(target=self.NEG_DLCWA_multi_A, args=(i_data_m, o_data_m, size, p, cache,))

				# --

				pc_list.append(pc)
				
		# --

		elif d in [self.BW]:
			for i in range(self.process_num):
				pc = Process(target=self.NEG_DLCWA_multi_B, args=(i_data_m, o_data_m, size, p, cache,))

				# --

				pc_list.append(pc)
		
		# --

		for pc in pc_list:
			pc.start()

		# --

		for pc in pc_list:
			pc.join()

		# --

		for pc in pc_list:
			pc.terminate()

		# --

		for pc in pc_list:
			del pc

		# --

		for s, o in cache.keys():
			try:
				self.cache['DLCWA', p, d][s, o] |= set(cache[s, o])

			except:
				self.cache['DLCWA', p, d][s, o] = set(cache[s, o])

		# --

		N = set(list(set(o_data_m.keys()))[0:size])

		# --

		return N

	# --

	def NEG_DLCWA_multi_A(self, i_data, o_data, size, p, cache):
		while True:
			try:
				s, o = i_data.get(False)

			except:
				break

			# -- 치환 후보 생성

			t_set = set([])

			try:
				if self.use_MST:
					t_set = self.get_mst(self.type_[o], self.class_parent)

				else:
					t_set = self.type_[o]

			except:
				cache[s, o] = set([])

				# --

				if len(o_data.keys()) >= size:
					break

				# --

				continue

			# --

			m_set = {}

			# --

			curr_set = set([s])
			next_set = set([])
			done_set = set([])

			for i in range(self.max_distance):
				for n in curr_set - done_set:
					try:
						self.e2t2e[n]

					except:
						continue

					# --

					for t in self.e2t2e[n]:
						if t in t_set:
							try:
								m_set[i] |= self.e2t2e[n][t]

							except:
								m_set[i] = set(self.e2t2e[n][t])

						# --

						next_set |= self.e2t2e[n][t]

				# --

				done_set |= curr_set

				# --

				curr_set = next_set
				next_set = set([])

			# --

			exclusion = set([s, o])

			for t in self.e2t2e[s]:
				if t in t_set:
					exclusion |= self.e2t2e[s][t]

			for i in m_set.keys():
				m_set[i] = m_set[i] - exclusion

			# -- 

			intersection = set([])

			for t in t_set:
				intersection |= self.p2t2o[p][t]

			for i in m_set.keys():
				m_set[i] = m_set[i] & intersection

			# --
			'''
			try:
				exclusion = set([s_ for s_, o_ in self.P_comp[p]['http://dbpedia.org/ontology/termPeriod', 'S-FW']])
				
				if s in exclusion:
					for i in m_set.keys():
						m_set[i] = set([])

			except:
				pass
			'''
			# --

			m_set_balanced = set([])

			for i in m_set.keys():
				m_set_balanced |= set(self.sample_data(m_set[i], self.n_rate))

			# -- 예제 생성

			gen_num = 0

			for m in self.shuffle_data(m_set_balanced):
				o_data[s, m] = True

				# --

				try:
					cache[s, o].add((s, m))

				except:
					cache[s, o] = set([(s, m)])

				# --

				gen_num += 1

				# --

				if gen_num >= self.n_rate:
					break

			# --

			if gen_num <= 0:
				cache[s, o] = set([])

			# --

			if len(o_data.keys()) >= size:
				break

	# --

	def NEG_DLCWA_multi_B(self, i_data, o_data, size, p, cache):
		while True:
			try:
				s, o = i_data.get(False)

			except:
				break

			# -- 치환 후보 생성

			t_set = set([])

			try:
				if self.use_MST:
					t_set = self.get_mst(self.type_[s], self.class_parent)

				else:
					t_set = self.type_[s]

			except:
				cache[s, o] = set([])

				# --

				if len(o_data.keys()) >= size:
					break

				# --
				
				continue

			# --

			m_set = {}

			# --

			curr_set = set([o])
			next_set = set([])
			done_set = set([])

			for i in range(self.max_distance):
				for n in curr_set - done_set:
					try:
						self.e2t2e[n]

					except:
						continue

					# --
					
					for t in self.e2t2e[n]:
						if t in t_set:
							try:
								m_set[i] |= self.e2t2e[n][t]

							except:
								m_set[i] = set(self.e2t2e[n][t])

						# --

						next_set |= self.e2t2e[n][t]

				# --

				done_set = curr_set

				# --

				curr_set = next_set
				next_set = set([])

			# --

			exclusion = set([s, o])

			for t in self.e2t2e[o]:
				if t in t_set:
					exclusion |= self.e2t2e[o][t]

			for i in m_set.keys():
				m_set[i] = m_set[i] - exclusion

			# --

			intersection = set([])

			for t in t_set:
				intersection |= self.p2t2s[p][t]

			for i in m_set.keys():
				m_set[i] = m_set[i] & intersection

			# --
			'''
			try:
				exclusion = set([s_ for s_, o_ in self.P_comp[p]['http://dbpedia.org/ontology/termPeriod', 'S-FW']])
				
				for i in m_set.keys():
					m_set[i] = m_set[i] - exclusion

			except:
				pass
			'''
			# --

			m_set_balanced = set([])

			for i in m_set.keys():
				m_set_balanced |= set(self.sample_data(m_set[i], self.n_rate))
				
			# -- 예제 생성

			gen_num = 0
			
			for m in self.shuffle_data(m_set_balanced):
				o_data[m, o] = True

				# --

				try:
					cache[s, o].add((m, o))

				except:
					cache[s, o] = set([(m, o)])

				# --

				gen_num += 1

				# --

				if gen_num >= self.n_rate:
					break

			# --

			if gen_num <= 0:
				cache[s, o] = set([])

			# --

			if len(o_data.keys()) >= size:
				break

	# --

	def compensate(self, E, E_comp, m_size):
		try:
			self.cache['compensate']

		except:
			self.cache['compensate'] = {}

		# --

		for s, o in E:
			try:
				self.cache['compensate'][s, o]

				continue

			except:
				pass

			# --

			try:
				for pb in self.s2p[s]:
					if len(E_comp[pb, 'S-FW']) < m_size:
						E_comp[pb, 'S-FW'].add((s, o))

			except:
				pass

			# --

			try:
				for pb in self.o2p[s]:
					if len(E_comp[pb, 'S-BW']) < m_size:
						E_comp[pb, 'S-BW'].add((s, o))

			except:
				pass

			# --

			try:
				for pb in self.s2p[o]:
					if len(E_comp[pb, 'O-FW']) < m_size:
						E_comp[pb, 'O-FW'].add((s, o))

			except:
				pass

			# --

			try:
				for pb in self.o2p[o]:
					if len(E_comp[pb, 'O-BW']) < m_size:
						E_comp[pb, 'O-BW'].add((s, o))

			except:
				pass
				
			# --

			self.cache['compensate'][s, o] = True
	
	# --

	def get_mst(self, type_set, class_parent):
		ancestor = set([])

		# --

		for t in type_set:
			ancestor |= self.get_ancestor(t, class_parent)

		# --

		return type_set - ancestor

	def get_ancestor(self, t, class_parent):
		return self.complete(t, class_parent) - set([t])

	def complete(self, t, class_parent):
		completed = set([t])
			
		# --

		while True:
			try:
				class_parent[t]

			except:
				break

			# --

			t = class_parent[t]

			# --

			completed.add(t)

		# --

		return completed

	# --

	def sample_data(self, data, size):
		sample = list(data)

		# --

		import random

		random.shuffle(sample)

		# --

		sample = sample[0:size]

		# --

		return sample

	def shuffle_data(self, data):
		shuffled = list(data)

		# --

		import random

		random.shuffle(shuffled)

		# --

		return shuffled

	# --

	def merge_type(self, type_list):
		merged_type = {}

		for type_ in type_list:
			for e in type_:
				for t in type_[e]:
					try:
						merged_type[e].add(t)

					except:
						merged_type[e] = set([t])

		return merged_type

	def merge_inst(self, inst_list):
		merged_inst = []

		for inst in inst_list:
			merged_inst += inst

		return merged_inst

# --

if __name__ == '__main__':
	main()