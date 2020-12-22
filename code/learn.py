def main():
	import argparse

	parser = argparse.ArgumentParser()

	parser.add_argument('rt')
	parser.add_argument('-cn')

	args = parser.parse_args()

	# --

	r_type_list = [r_type for r_type in args.rt]

	print(r_type_list)

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

	R_M = Rule_Model(conf)

	# --

	import time

	b_t = time.time()

	# --

	for r_type in r_type_list:
		R_learned = R_M.learn(r_type) # 'P', 'N'

		# --

		if r_type == 'P':
			o_name = 'R-P.tsv'

		elif r_type == 'N':
			o_name = 'R-N.tsv'

		# --

		with open(output + '/' + o_name, 'w+') as o_file:
			for p in sorted(R_learned):
				for r, w_n, g_cover, v_cover, a, b, c, d in sorted(R_learned[p], key=lambda x: x[1]):
					import json

					# --

					o_file.write('\t'.join([p, json.dumps(r, ensure_ascii=False), str(w_n), str(g_cover), str(v_cover), str(a), str(b), str(c), str(d)]) + '\n')

		# --

		if r_type == 'P':
			o_name = 'R-P-simple.tsv'

		elif r_type == 'N':
			o_name = 'R-N-simple.tsv'

		# --

		with open(output + '/' + o_name, 'w+') as o_file:
			for p in sorted(R_learned):
				for r, w_n, g_cover, v_cover, a, b, c, d in sorted(R_learned[p], key=lambda x: x[1]):
					import json

					# --

					o_file.write('\t'.join([RDF.remove_prefix(p), R_M.simplify(r, r_type), str(round(w_n, 4)), str(round(g_cover, 4)), str(round(v_cover, 4)), str(a), str(b), str(c), str(d)]) + '\n')

	# --

	e_t = time.time()

	print('time', e_t - b_t)

# --

class Rule_Model:
	FW = 1
	BW = -1
	UD = 0

	# --

	class_parent = {}

	# --

	type_ = {}

	# -- 전체 학습 데이터

	p_list = []

	# --

	p2P = {}
	p2N = {}

	# --

	p2G = {}
	p2V = {}

	# --

	graph_g = {}

	# -- 현재 학습 데이터

	p = None

	# --

	G = None
	V = None

	# --

	graph_l = {}

	# --

	cache = {}

	# ----

	def __init__(self, conf, used_for='learn'):
		input_ = conf['inter-input']
		output = conf['inter-output']

		# --

		class_parent_path = conf['class-parent-path']
	
		type_path = conf['type-path']

		if used_for == 'learn':
			inst_path = conf['inst-path-B']

		elif used_for == 'filter':
			inst_path = conf['inst-path-C']

		# --

		self.use_OT = conf['use-OT']
		self.use_MST = conf['use-MST']

		p_path = conf['p-path']

		self.n_rate = conf['n-rate']
		self.n_size = conf['n-size']

		self.weight = conf['weight']

		self.max_path_len = conf['max-path-len']
		self.a = conf['a']
		self.b = conf['b']
		self.c = conf['c']
		self.min_cover = conf['min-cover']
		self.min_penalty = conf['min-penalty']

		self.process_num = conf['process-num']

		# --

		from module.TSV import TSV

		TSV = TSV()

		from module.RDF import RDF

		RDF = RDF()

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

		if self.use_OT:
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

		self.inst = self.merge_inst(inst_list)

		# -- 전역 그래프

		for s, p, o_v, o_t in self.inst:
			# -- 오브젝트

			if o_t in ['object']:
				n_s = (s, 'object')
				n_o = (o_v, o_t)

				# --

				self.insert_triple(n_s, p, n_o, self.graph_g)

			# -- 리터럴 (범위: 정수, 실수, 날짜)

			else:
				o_v = RDF.parse_literal(o_v, o_t)

				# --

				from datetime import datetime

				if type(o_v) in [int, float, datetime]:
					n_s = (s, 'object')
					n_o = (o_v, o_t)

					# --

					self.insert_triple(n_s, p, n_o, self.graph_g)

		# -- 옳은 예제

		for s, p, o in TSV.read_list(output + '/P.tsv'):
			try:
				self.p2P[p].add((s, o))

			except:
				self.p2P[p] = set([(s, o)])

		# -- 틀린 예제

		for s, p, o in TSV.read_list(output + '/N.tsv'):
			try:
				self.p2N[p].add((s, o))

			except:
				self.p2N[p] = set([(s, o)])

		# -- 목표 규칙 확인
		'''
		for s, p, o, l in TSV.read_list('../input/test-real.tsv'):
			s = 'http://dbpedia.org/resource/' + s
			o = 'http://dbpedia.org/resource/' + o
			p = 'http://dbpedia.org/ontology/' + p

			# --

			if l in ['o']:
				try:
					self.p2P[p].add((s, o))

				except:
					self.p2P[p] = set([(s, o)])

			if l in ['x']:
				try:
					self.p2N[p].add((s, o))

				except:
					self.p2N[p] = set([(s, o)])
		'''
		# -- 프로퍼티

		self.p_list = []

		if p_path:
			for path in p_path:
				with open(path) as i_file:
					import json

					# --

					self.p_list += json.loads(i_file.read())

			# --

			self.p_list = sorted(set(self.p_list) & self.p2P.keys())
			
		else:
			self.p_list = sorted(self.p2P.keys())

	# --

	def learn(self, r_type):
		if r_type not in ['P', 'N']:
			raise Exception('r_type')

		# --

		R_learned = {}

		# -- 트레이닝 데이터

		for p in self.p_list:
			try:
				P = self.p2P[p]

			except:
				P = set([])

			# --

			try:
				N = self.p2N[p]

			except:
				N = set([])

			# --

			if r_type in ['P']:
				self.p2G[p] = P
				self.p2V[p] = N

			elif r_type in ['N']:
				self.p2G[p] = N
				self.p2V[p] = P

		# --

		p_num = 1

		for p in self.p_list:
			# -- 학습 변수 초기화

			self.p = p

			print(self.p, p_num, len(self.p_list))
			
			p_num += 1

			# --

			self.G = self.p2G[self.p]
			self.V = self.p2V[self.p]

			print('G', len(self.G))
			print('V', len(self.V))

			# --

			self.init_cache()

			# --

			self.init_graph()

			# -- 지역 그래프 생성

			from multiprocessing import Manager, Process

			# --

			i_data = Manager().Queue()

			for s, o in self.G | self.V:
				n_s = (s, 'object')
				n_o = (o, 'object')

				# --

				i_data.put((n_s, n_o), False)

			print(1, end=' ')

			# --

			o_data = Manager().dict()

			# --

			pc_list = []

			# --

			for i in range(self.process_num):
				pc = Process(target=self.construct_graph_multi, args=(i_data, o_data, r_type,))

				# --

				pc_list.append(pc)

			print(2, end=' ')

			# --

			for pc in pc_list:
				pc.start()

			print(3)

			# --

			while True:
				print('LG', len(o_data.keys()), len(self.G | self.V))

				# --

				if len(o_data.keys()) >= len(self.G | self.V):
					break

				# --

				import time

				time.sleep(30)

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

			for n_s, n_o in o_data.keys():
				self.graph_l[n_s, n_o] = dict(o_data[n_s, n_o])

				self.graph_l[n_o, n_s] = self.graph_l[n_s, n_o]

			# --

			print('LG', len(o_data.keys()), len(self.G | self.V))

			# -- 규칙 학습

			R_W = set([])

			# --

			if self.weight in ['margin-weight']:
				# -- 기본 규칙 학습

				r_base = ((0, 1, self.p, self.BW), (1, 0, self.p, self.FW))

				# --

				w, g_cover, v_cover, a, b, c, d = self.normal_weight(set([r_base]))

				# --

				R_W.add((r_base, w, g_cover, v_cover, a, b, c, d))

				# -- 확장 규칙 학습

				for i in range(self.max_path_len):
					r_len = i + 1

					# -- 규칙 생성

					R = self.generate_rule(r_len) - set([r_base])

					# --

					if len(R) <= 0:
						continue

					# --

					print('RG', r_len, len(R))

					# -- 규칙 가중

					self.C_R_G = set([])
					self.C_R_V = set([])
					self.U_R_V = set([])

					# --

					while len(R) >= 1:
						r, w_m = self.argmin_weight(R)

						# --

						if not r:
							break

						# --

						w_n, g_cover, v_cover, a, b, c, d = self.normal_weight(set([r]))

						# --

						R_W.add((r, w_n, g_cover, v_cover, a, b, c, d))

						# --

						self.C_R_G |= self.C_E(set([r]), self.G - self.C_R_G)
						self.C_R_V |= self.C_E(set([r]), self.V - self.C_R_V)
						self.U_R_V |= self.U_E(set([r]), self.V - self.U_R_V)

						# --

						print('RW', '|', r_type, r_len, '|', len(R_W), len(R), '|', self.simplify(r, r_type), round(w_m, 4), round(len(self.C_R_G) / len(self.G), 4))			

			# --
			
			elif self.weight in ['normal-weight-T1', 'normal-weight-T2', 'constr-weight']:
				# -- 규칙 생성

				R = set([])

				for i in range(self.max_path_len):
					r_len = i + 1

					# --

					R |= self.generate_rule(r_len)

				# --

				if len(R) <= 0:
					continue

				# --

				print('RG', len(R))

				# -- 규칙 가중

				for r, w, g_cover, v_cover, a, b, c, d in self.sortby_weight(R, r_type):
					R_W.add((r, w, g_cover, v_cover, a, b, c, d))
					
					# --

					print('RW', '|', r_type, len(r) - 1, '|', len(R_W), len(R), '|', self.simplify(r, r_type), round(w, 4), round(g_cover, 4), round(v_cover, 4))

			# -- 규칙 저장

			for r, w, g_cover, v_cover, a, b, c, d in R_W:
				try:
					R_learned[self.p].add((r, w, g_cover, v_cover, a, b, c, d))

				except:
					R_learned[self.p] = set([(r, w, g_cover, v_cover, a, b, c, d)])
				
		# --

		return R_learned

	# ----

	def construct_graph_multi(self, i_data, o_data, r_type):
		while True:
			try:
				n_s, n_o = i_data.get(False)

			except:
				break

			# --

			if r_type in ['P']:
				o_data[n_s, n_o] = self.construct_graph(n_s, n_o, NEC=False, LC=False)

			elif r_type in ['N']:
				o_data[n_s, n_o] = self.construct_graph(n_s, n_o, NEC=True, LC=True)

	def construct_graph(self, n_s, n_o, NEC=True, LC=True):
		# -- 캐싱

		try:
			return self.graph_l[n_s, n_o]

		except:
			self.graph_l[n_s, n_o] = {}

		# -- 지역 그래프 생성

		family = {n_s: set([n_s]), n_o: set([n_o])}

		oj_set = {n_s: set([n_s]), n_o: set([n_o])}

		dt_set = {n_s: set([]), n_o: set([])}

		# -- 중간 링크 연결

		last_set = {}

		for n in [n_s, n_o]:
			curr_set = set([n])
			next_set = set([])
			done_set = set([])

			# --

			for i in range(max(self.max_path_len - 2, 1)):
				for n_c in curr_set - done_set:
					neighbor_FW = set([])
					neighbor_BW = set([])

					# --
					# try-except 이유: 테스트 케이스에서 프로퍼티가 없는 개체 존재 가능
					# --
					try:
						for n_n, p, d in self.graph_g['n2npd'][n_c]:
							if d in [self.FW]:
								neighbor_FW.add(n_n)

							elif d in [self.BW]:
								neighbor_BW.add(n_n)

					except:
						continue

					neighbor_FW = set(self.sample_data(neighbor_FW, self.n_size))
					neighbor_BW = set(self.sample_data(neighbor_BW, self.n_size))

					# --

					neighbor_A = neighbor_FW | neighbor_BW
					neighbor_B = set(self.sample_data(neighbor_FW, 250)) | set(self.sample_data(neighbor_BW, 250))

					# --

					for n_n in neighbor_A:
						for p, d in self.graph_g['nn2pd'][n_c, n_n]:
							if d in [self.FW]:
								self.insert_triple(n_c, p, n_n, self.graph_l[n_s, n_o])

							elif d in [self.BW]:
								self.insert_triple(n_n, p, n_c, self.graph_l[n_s, n_o])

						# --

						if i == 0:
							try:
								family[n].add(n_n)

							except:
								family[n] = set([n_n])

					# --

					for n_n in neighbor_B:
						if n_n[1] in ['object']:
							try:
								oj_set[n].add(n_n)

							except:
								oj_set[n] = set([n_n])

					# --

					for n_n in neighbor_A:
						from datetime import datetime

						if type(n_n[0]) in [int, float, datetime]:
							try:
								dt_set[n].add(n_n)

							except:
								dt_set[n] = set([n_n])

					# --

					next_set |= neighbor_A

				# --

				done_set |= curr_set

				# --
				
				curr_set = next_set
				next_set = set([])

			# --

			last_set[n] = curr_set

		# -- 말단 링크 연결 / 보틀넥

		for l_s in last_set[n_s]:
			for f_o in family[n_o]:
				try:
					for p, d in self.graph_g['nn2pd'][l_s, f_o]:
						if d in [self.FW]:
							self.insert_triple(l_s, p, f_o, self.graph_l[n_s, n_o])

						elif d in [self.BW]:
							self.insert_triple(f_o, p, l_s, self.graph_l[n_s, n_o])

				except:
					pass

		# --

		for l_o in last_set[n_o]:
			for f_s in family[n_s]:
				try:
					for p, d in self.graph_g['nn2pd'][l_o, f_s]:
						if d in [self.FW]:
							self.insert_triple(l_o, p, f_s, self.graph_l[n_s, n_o])

						elif d in [self.BW]:
							self.insert_triple(f_s, p, l_o, self.graph_l[n_s, n_o])

				except:
					pass

		# -- != 연결 / 보틀넥

		if NEC:
			for n in oj_set[n_s] - oj_set[n_o] | set([n_s]):
				for m in oj_set[n_o] - oj_set[n_s] | set([n_o]):
					if n == m:
						continue

					if n == n_s and m == n_o:
						continue

					if n == n_o and m == n_s:
						continue

					# --

					n_v, n_t = n
					m_v, m_t = m

					# --

					try:
						if self.use_MST:
							n_t_set = self.get_mst(self.type_[n_v], self.class_parent)
							m_t_set = self.get_mst(self.type_[m_v], self.class_parent)

						else:
							n_t_set = self.type_[n_v]
							m_t_set = self.type_[m_v]

					except:
						continue

					# --

					if self.is_intersect(n_t_set, m_t_set): 
						if n != m:
							self.insert_triple(n, '!=', m, self.graph_l[n_s, n_o], direct=False)

		# -- > < 연결

		if LC:
			for n in dt_set[n_s]:
				for m in dt_set[n_o]:
					n_v, n_t = n
					m_v, m_t = m

					# --

					if n_t == m_t:
						if n_v > m_v:
							self.insert_triple(n, '>', m, self.graph_l[n_s, n_o])

						elif m_v > n_v:
							self.insert_triple(m, '>', n, self.graph_l[n_s, n_o])

		# --

		self.graph_l[n_o, n_s] = self.graph_l[n_s, n_o]

		# --

		return self.graph_l[n_s, n_o]

	def generate_rule(self, r_len):
		R = set([])

		# --

		for s, o in self.G:
			n_s = (s, 'object')
			n_o = (o, 'object')

			# --

			r_inst = tuple([(n_o, n_s, self.p, self.BW)])

			# --

			R_inst = {r_inst: True}

			# --

			for i in range(r_len):
				for r_inst in dict(R_inst):
					del R_inst[r_inst]

					# --

					head = r_inst[0]
					body = r_inst[1:]
					tail = r_inst[-1]

					# --

					n_s = head[1]
					n_o = head[0]
					n_f = tail[1]

					# --

					n_body = set([a for a, b, p, d in body] + [b for a, b, p, d in body])
					p_body = set([p for a, b, p, d in body])

					# --

					try:
						for n, p, d in self.graph_l[n_s, n_o]['n2npd'][n_f]:
							if n in n_body:
								continue

							# --

							if p in p_body and p == '!=':
								continue

							# --

							if p in p_body and p == '>':
								continue

							# --

							r_inst_expanded = tuple(list(r_inst) + [(n_f, n, p, d)])

							# --

							R_inst[r_inst_expanded] = True

					except:
						pass

			# --

			for r_inst in dict(R_inst):
				r = self.generalize(r_inst)

				# --

				if self.is_valid(r):
					R.add(r)

			# --

			for r_inst in dict(R_inst):
				del R_inst[r_inst]

			del R_inst

		# --

		return R

	def argmin_weight(self, R):
		from multiprocessing import Manager, Process

		# --

		i_data = Manager().Queue()

		for r in R:
			i_data.put(r, False)

		# --
		
		o_data = Manager().dict()

		# --

		pc_list = []

		for i in range(self.process_num):
			pc = Process(target=self.argmin_weight_multi, args=(i_data, o_data))

			# --

			pc_list.append(pc)

		# --

		for pc in pc_list:
			pc.start()

		# --

		for pc in pc_list:
			pc.join()

		# --

		sorted_result = sorted(o_data.keys(), key=lambda x: x[1])

		# --

		for r, w in list(sorted_result):
			if w >= 0.0:
				sorted_result.remove((r, w))

		# --

		if len(sorted_result) >= 1:
			argmin_result = sorted_result[0]

			# --

			sorted_result.remove(argmin_result)

		else:
			argmin_result = (None, None)

		# --

		remain_result = [r for r, w in sorted_result]

		# --

		for r in set(R):
			if r not in remain_result:
				R.remove(r)

		# --

		return argmin_result

	def argmin_weight_multi(self, i_data, o_data):
		while True:
			try:
				r = i_data.get(False)

			except:
				break

			# --

			w = self.margin_weight(r)

			# --

			o_data[r, w] = True

	def normal_weight(self, R):
		C_r_G = self.C_N(R, self.G)
		G = len(self.G)

		C_r_V = self.C_N(R, self.V)
		U_r_V = self.U_N(R, self.V)

		# --

		try:
			g_cover = C_r_G / G

		except:
			g_cover = 0.0

		# --

		try:
			v_cover = C_r_V / U_r_V

		except:
			v_cover = 0.0

		# --

		w = self.a * (1.0 - g_cover) + self.b * v_cover

		# --

		return w, g_cover, v_cover, C_r_G, G, C_r_V, U_r_V

	def margin_weight(self, r):
		C_r_G = len(self.C_E(set([r]), self.G - self.C_R_G))
		G = len(self.G)
		
		C_rR_V = len(self.C_E(set([r]), self.V - self.C_R_V) | self.C_R_V)
		U_rR_V = len(self.U_E(set([r]), self.V - self.U_R_V) | self.U_R_V)
		
		C_R_V = len(self.C_R_V)
		U_R_V = len(self.U_R_V)

		# --

		try:
			g_cover = C_r_G / G

		except:
			g_cover = 0.0

		# --

		v_cover = 0.0

		# --

		try:
			v_cover += C_rR_V / U_rR_V

		except:
			pass

		# --

		try:
			v_cover -= C_R_V / U_R_V

		except:
			pass

		# --

		w = self.b * v_cover - self.a * g_cover 

		# --

		return w

	def sortby_weight(self, R, r_type):
		from multiprocessing import Manager, Process

		# --

		i_data = Manager().Queue()

		for r in R:
			i_data.put(r, False)

		# --
		
		o_data = Manager().dict()

		# --

		pc_list = []

		for i in range(self.process_num):
			pc = Process(target=self.sortby_weight_multi, args=(i_data, o_data, r_type,))

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

		R_sorted = sorted(o_data.keys(), key=lambda x: x[1])

		# --

		return R_sorted

	def sortby_weight_multi(self, i_data, o_data, r_type):
		while True:
			try:
				r = i_data.get(False)

			except:
				break

			# --

			if self.weight in ['normal-weight-T1']:
				w, g_cover, v_cover, a, b, c, d = self.normal_weight_T1(set([r]))

			elif self.weight in ['normal-weight-T2']:
				w, g_cover, v_cover, a, b, c, d = self.normal_weight_T2(set([r]))

			elif self.weight in ['constr-weight']:
				w, g_cover, v_cover, a, b, c, d = self.constr_weight(set([r]), r_type)

			# --

			o_data[r, w, g_cover, v_cover, a, b, c, d] = True

	def normal_weight_T1(self, R):
		C_r_G = self.C_N(R, self.G)
		U_r_G = self.U_N(R, self.G)

		# --

		try:
			g_cover = C_r_G / U_r_G

		except:
			g_cover = 0.0

		# --

		w = 1.0 - g_cover

		# --

		return w, g_cover, 0.0, C_r_G, U_r_G, 0, 0

	def normal_weight_T2(self, R):
		C_r_G = self.C_N(R, self.G)
		U_r_G = self.U_N(R, self.G)

		C_r_V = self.C_N(R, self.V)
		U_r_V = self.U_N(R, self.V)

		# --

		try:
			g_cover = C_r_G / U_r_G

		except:
			g_cover = 0.0

		# --

		try:
			v_cover = C_r_V / U_r_V

		except:
			v_cover = 0.0

		# --

		w = self.a * (1.0 - g_cover) + self.b * v_cover

		# --

		return w, g_cover, v_cover, C_r_G, U_r_G, C_r_V, U_r_V

	def constr_weight(self, R, r_type):
		C_r_G = self.C_N(R, self.G)
		U_r_G = self.U_N(R, self.G)

		C_r_V = self.C_N(R, self.V)
		U_r_V = self.U_N(R, self.V)

		# --

		try:
			g_cover = C_r_G / U_r_G

		except:
			g_cover = 0.0

		# --

		try:
			v_cover = C_r_V / U_r_V

		except:
			v_cover = 0.0

		# --

		w = self.a * (1.0 - g_cover) + self.b * v_cover

		# --

		w = 1.0 - max((g_cover - (1.0 / self.c) * v_cover) / g_cover, self.min_penalty) * (1.0 - w)

		# --

		if r_type == 'P':
			if C_r_G <= self.min_cover:
				w = 1.0 - self.min_penalty * (1.0 - w)

		elif r_type == 'N':
			if C_r_G <= self.min_cover * self.n_rate:
				w = 1.0 - self.min_penalty * (1.0 - w)

		# --

		return w, g_cover, v_cover, C_r_G, U_r_G, C_r_V, U_r_V

	def C_E(self, R, E):
		covered = set([])

		# --

		for s, o in E:
			for r in R:
				n_s = (s, 'object')
				n_o = (o, 'object')

				# --

				if self.is_covered(n_s, n_o, r):
					covered.add((s, o))

					break

		# --

		return covered

	def U_E(self, R, E):
		covered = set([])

		# --

		for s, o in E:
			for r in R:
				n_s = (s, 'object')
				n_o = (o, 'object')

				# --
				
				if self.is_covered(n_s, n_o, self.unbound(r)):
					covered.add((s, o))

					break

		# --

		return covered

	def C_N(self, R, E):
		covered = 0

		# --

		for s, o in E:
			for r in R:
				n_s = (s, 'object')
				n_o = (o, 'object')

				# --

				if self.is_covered(n_s, n_o, r):
					covered += 1

					break

		# --

		return covered

	def U_N(self, R, E):
		covered = 0

		# --

		for s, o in E:
			for r in R:
				n_s = (s, 'object')
				n_o = (o, 'object')

				# --
				
				if self.is_covered(n_s, n_o, self.unbound(r)):
					covered += 1

					break

		# --

		return covered

	def is_covered(self, n_s, n_o, r):
		if self.get_binding(n_s, n_o, r):
			covered = True

		else:
			covered = False

		# --

		return covered

	def get_binding(self, n_s, n_o, r):
		head = r[0]
		body = r[1:]

		# --

		x = head[1]
		y = head[0]

		# --

		if x == y and n_s != n_o:
			full_binding = None

			# --

			return full_binding

		# --

		binding = {y: n_o, x: n_s}

		# --

		binding_list = [binding]

		# --

		for v_a, v_b, p, d in body:
			for binding in list(binding_list):
				binding_list.remove(binding)

				# --

				try:
					n_a = binding[v_a]

				except:
					n_a = None

				try:
					n_b = binding[v_b]

				except:
					n_b = None

				# --

				if n_a and n_b:
					try:
						if (p, d) in self.graph_l[n_s, n_o]['nn2pd'][n_a, n_b]:
							binding_list.append(dict(binding))

					except:
						pass

				elif n_a:
					try:
						for n_b in self.graph_l[n_s, n_o]['npd2n'][n_a, p, d]:
							if self.is_bound(r):
								if n_b in binding.values():
									continue

							# --

							binding[v_b] = n_b

							# --

							binding_list.append(dict(binding))

					except:
						pass

				elif n_b:
					try:
						for n_a in self.graph_l[n_s, n_o]['npd2n'][n_b, p, d * -1]:	
							if self.is_bound(r):
								if n_a in binding.values():
									continue

							# --

							binding[v_a] = n_a

							# --

							binding_list.append(dict(binding))

					except:
						pass

		# --

		full_binding = None

		# --

		for binding in binding_list:
			if len(binding.keys()) == len(self.get_variable(r)):
				full_binding = dict(binding)

				break

		# --

		return full_binding
	
	# ----

	def insert_triple(self, n_s, p, n_o, graph, direct=True):
		if direct == True:
			FW = self.FW
			BW = self.BW

		else:
			FW = self.UD
			BW = self.UD

		# --

		try:
			graph['n2npd']

		except:
			graph['n2npd'] = {}

		try:
			graph['n2npd'][n_s].add((n_o, p, FW))

		except:
			graph['n2npd'][n_s] = set([(n_o, p, FW)])

		try:
			graph['n2npd'][n_o].add((n_s, p, BW))

		except:
			graph['n2npd'][n_o] = set([(n_s, p, BW)])

		# --

		try:
			graph['nn2pd']

		except:
			graph['nn2pd'] = {}

		try:
			graph['nn2pd'][n_s, n_o].add((p, FW))

		except:
			graph['nn2pd'][n_s, n_o] = set([(p, FW)])

		try:
			graph['nn2pd'][n_o, n_s].add((p, BW))

		except:
			graph['nn2pd'][n_o, n_s] = set([(p, BW)])

		# --

		try:
			graph['npd2n']

		except:
			graph['npd2n'] = {}

		try:
			graph['npd2n'][n_s, p, FW].add(n_o)

		except:
			graph['npd2n'][n_s, p, FW] = set([n_o])

		try:
			graph['npd2n'][n_o, p, BW].add(n_s)

		except:
			graph['npd2n'][n_o, p, BW] = set([n_s])

	def generalize(self, r_inst):
		# -- 노드에 변수를 할당

		n2v = {}

		v = 0

		for n_a, n_b, p, d, in r_inst:
			try:
				n2v[n_a]

			except:
				n2v[n_a] = v

				v += 1

			# --

			try:
				n2v[n_b]

			except:
				n2v[n_b] = v

				v += 1

		# -- 노드를 변수로 치환

		r = []

		for n_a, n_b, p, d, in r_inst:
			r.append((n2v[n_a], n2v[n_b], p, d))

		# --

		r = tuple(r)

		# --

		return r

	def is_valid(self, r):
		head = r[0]
		body = r[1:]

		# --

		x = head[1]
		y = head[0]

		# -- x y 사이 경로

		if body[0][0] != x:
			return False

		if body[-1][1] != y:
			return False

		# --

		v_cnt = {}

		for v_a, v_b, p, d in r:
			try:
				v_cnt[v_a] += 1

			except:
				v_cnt[v_a] = 1

			try:
				v_cnt[v_b] += 1

			except:
				v_cnt[v_b] = 1

		# -- 순환 없는 닫힌 형태

		for v in v_cnt:
			if v_cnt[v] != 2:
				return False

		# -- !=, > 한번 허용

		ne_cnt = 0
		lc_cnt = 0

		for v_a, v_b, p, d in body:
			if p == '!=':
				ne_cnt += 1

				# --

				if ne_cnt >= 2:
					return False

			# --

			elif p == '>':
				lc_cnt += 1

				# --

				if lc_cnt >= 2:
					return False

		# --

		return True

	def unbound(self, r):
		r_unbounded = []

		# --

		head = r[0]
		body = r[1:]

		# --

		x = head[1]
		y = head[0]

		# --

		r_unbounded.append(head)

		# --

		v_max = -1

		for v_a, v_b, p, d in body:
			if v_a > v_max:
				v_max = v_a

			if v_b > v_max:
				v_max = v_b

		# --

		v_new = v_max + 1

		for v_a, v_b, p, d in body:
			if v_a in [x, y] and v_b not in [x, y]:
				r_unbounded.append((v_a, v_new, p, d))

				v_new += 1

			elif v_a not in [x, y] and v_b in [x, y]:
				r_unbounded.append((v_new, v_b, p, d))

				v_new += 1

			elif v_a in [x, y] and v_b in [x, y]:
				r_unbounded.append((v_a, v_new, p, d))

				v_new += 1

				r_unbounded.append((v_new, v_b, p, d))

				v_new += 1

				#r_unbounded.append((v_a, v_b, p, d))

		# --

		r_unbounded = tuple(r_unbounded)

		# --

		return r_unbounded

	def is_bound(self, r):
		bound = True

		# --

		head = r[0]
		body = r[1:]

		# --

		x = head[1]
		y = head[0]

		# --

		v_f = x

		# --

		for v_a, v_b, p, d in body:
			if v_a != v_f:
				bound = False

			# --

			v_f = v_b

		# --

		if v_f != y:
			bound = False

		# --

		return bound

	def is_variable(self, x):
		if type(x) == int:
			return True

		else:
			return False

	def is_constant(self, x):
		if not self.is_variable(x):
			return True

		else:
			return False

	def get_variable(self, r):
		v_set = set([])

		# --

		for v_a, v_b, p, d in r:
			v_set.add(v_a)
			v_set.add(v_b)

		# --

		return v_set

	def sample_data(self, data, size):
		sample = list(data)

		# --

		import random

		random.shuffle(sample)

		# --

		sample = sample[0:size]

		# --

		return sample

	def is_intersect(self, set_a, set_b):
		if len(set_a) > len(set_b):
			smaller, bigger = set_b, set_a

		else:
			smaller, bigger = set_a, set_b

		# --

		for e in smaller:
			if e in bigger:
				return True

		# --

		return False

	# ----

	def init_cache(self):
		for t in set(self.cache.keys()):
			del self.cache[t]

		# --

		self.cache = {}

	def init_graph(self):
		for n_s, n_o in set(self.graph_l.keys()):
			del self.graph_l[n_s, n_o]

		# --

		self.graph_l = {}

	# ----

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

	def merge_type(self, type_list):
		merged_type = {}

		# --

		for type_ in type_list:
			for e in type_:
				for t in type_[e]:
					try:
						merged_type[e].add(t)

					except:
						merged_type[e] = set([t])

		# --

		return merged_type

	def merge_inst(self, inst_list):
		merged_inst = []

		# --

		for inst in inst_list:
			merged_inst += inst

		# --

		return merged_inst

	# --

	def simplify(self, r, r_type):
		r_simple = []

		# --

		from module.RDF import RDF

		RDF = RDF()

		# --

		for i in range(len(r)):
			v1, v2, p, d = r[i]

			# --

			if d in [self.FW]:
				atom = '(' + ' '.join([str(v1), RDF.remove_prefix(p), str(v2)]) + ')'
			
			elif d in [self.BW]:
				atom = '(' + ' '.join([str(v2), RDF.remove_prefix(p), str(v1)]) + ')'

			elif d in [self.UD]:
				atom = '(' + ' '.join([str(v1), RDF.remove_prefix(p), str(v2)]) + ')'

			# --

			if i == 0:
				if r_type in ['P']:
					r_simple.append(atom)

					r_simple.append('<')

				elif r_type in ['N']:
					r_simple.append('!')

					r_simple.append(atom)

					r_simple.append('<')

			elif i < len(r) - 1:
				r_simple.append(atom)

				r_simple.append('&')

			else:
				r_simple.append(atom)

		# --

		r_simple = ' '.join(r_simple)

		# --

		return r_simple

# --

if __name__ == '__main__':
	main()