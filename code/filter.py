def main():
	import argparse

	parser = argparse.ArgumentParser()

	parser.add_argument('-i')
	parser.add_argument('-o')
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

	try:
		input_ = args.i
		output = args.o

	except:
		input_ = conf['input']
		output = conf['output']

	print(input_)
	print(output)

	# --

	from module.TSV import TSV

	TSV = TSV()

	# --

	row_list = TSV.read_list(input_)

	# --

	rf = RF(conf)

	# --

	result = []

	iter_num = 1

	for row in row_list:
		try:
			s = row[0]
			p = row[1]
			o = row[2]

			etc = row[3:]

		except:
			continue

		# --

		label, score, expl = rf.validate(s, p, o)

		# --

		result.append([s, p, o, etc, label, score, expl])

		# --

		if iter_num % 1000 == 0:
			print(iter_num, len(row_list))

		iter_num += 1

	# --

	with open(output + '/result-positive.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			if label in [rf.T]:
				o_file.write('\t'.join([s, p, o] + etc) + '\n')

	with open(output + '/result-negative.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			if label in [rf.F]:
				o_file.write('\t'.join([s, p, o] + etc) + '\n')

	with open(output + '/result-unable.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			if label in [rf.U]:
				o_file.write('\t'.join([s, p, o] + etc) + '\n')

	with open(output + '/result-not-negative.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			if label not in [rf.F]:
				o_file.write('\t'.join([s, p, o] + etc) + '\n')

	# -- 성능 측정 용도

	with open(output + '/result-scored.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			if score == None:
				score = ''

			else:
				score = str(score)

			# --

			o_file.write('\t'.join([s, p, o, score]) + '\n')

	with open(output + '/result-labeled.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			o_file.write('\t'.join([s, p, o, label]) + '\n')

	# -- 분석 용도

	with open(output + '/result-explained-A.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			if score == None:
				score = ''

			else:
				score = str(score)

			# --

			evidence, s_p, s_n, p_size, n_size = expl

			expl = ' | '.join([evidence, str(s_p), str(s_n), str(p_size), str(n_size)])

			# --

			o_file.write('\t'.join([s, p, o] + etc + [label, score, expl]) + '\n')

	with open(output + '/result-explained-B.tsv', 'w+') as o_file:
		for s, p, o, etc, label, score, expl in result:
			if score == None:
				score = ''

			else:
				score = str(round(score, 4))

			# --

			evidence, s_p, s_n, p_size, n_size = expl

			expl = ' | '.join([evidence, str(round(s_p, 4)), str(round(s_n, 4)), str(p_size), str(n_size)])

			# --

			o_file.write('\t'.join([s, p, o] + etc + [label, score, expl]) + '\n')

# --

class RF:
	T = 'o'
	F = 'x'
	U = '?'

	# --

	R_P = {}
	R_N = {}

	# --

	def __init__(self, conf):
		output = conf['inter-output']

		# --

		self.r_prefix = conf['r-prefix']
		self.o_prefix = conf['o-prefix']

		# --

		self.a = conf['a']
		self.b = conf['b']
		self.c = conf['c']
		self.min_cover = conf['min-cover']
		self.min_penalty = conf['min-penalty']

		# --

		self.evidence_type = conf['evidence-type']

		self.score_threshold_A = conf['score-threshold-A']
		self.score_threshold_B = conf['score-threshold-B']

		# --

		from learn import Rule_Model
		
		self.R_M = Rule_Model(conf, used_for='filter')

		# --

		if self.evidence_type in ['P', 'PN']:
			with open(output + '/R-P.tsv') as i_file:
				for line in i_file.readlines():
					line = line.strip()

					# --

					import re

					p, r, w, g_cover, v_cover, a, b, c, d = re.split('\t', line)

					# --

					import json

					r = tuple([tuple(atom) for atom in json.loads(r)])
					w = float(w)

					g_cover = float(g_cover)
					v_cover = float(v_cover)
					a = int(a)
					b = int(b)
					c = int(c)
					d = int(d)

					# --

					try:
						self.R_P[p].append([r, w, g_cover, v_cover, a, b, c, d])

					except:
						self.R_P[p] = [[r, w, g_cover, v_cover, a, b, c, d]]

				# --

				for p in self.R_P:
					self.R_P[p] = sorted(self.R_P[p], key=lambda x: x[1])

		# --

		if self.evidence_type in ['N', 'PN']:
			with open(output + '/R-N.tsv') as i_file:
				for line in i_file.readlines():
					line = line.strip()

					# --

					import re

					p, r, w, g_cover, v_cover, a, b, c, d = re.split('\t', line)

					# --

					import json

					r = tuple([tuple(atom) for atom in json.loads(r)])
					w = float(w)

					g_cover = float(g_cover)
					v_cover = float(v_cover)
					a = int(a)
					b = int(b)
					c = int(c)
					d = int(d)

					# --

					try:
						self.R_N[p].append([r, w, g_cover, v_cover, a, b, c, d])

					except:
						self.R_N[p] = [[r, w, g_cover, v_cover, a, b, c, d]]

				# --

				for p in self.R_N:
					self.R_N[p] = sorted(self.R_N[p], key=lambda x: x[1])

	# --

	def validate(self, s, p, o, used_for='eval'):
		from module.RDF import RDF

		RDF = RDF()

		# --

		if 'http://' not in s:
			s_ = self.r_prefix + s

		else:
			s_ = s

		if 'http://' not in p:
			p_ = self.o_prefix + p

		else:
			p_ = p

		if 'http://' not in o:
			o_ = self.r_prefix + o

		else:
			o_ = o

		# -- 규칙 유무 검사

		c1 = False

		try:
			self.R_P[p_]

		except:
			c1 = True

		# --

		c2 = False

		try:
			self.R_N[p_]

		except:
			c2 = True

		# --

		if c1 and c2:
			if used_for in ['eval']:
				return [self.U, 0.5, ['규칙 없음', 0.0, 0.0, 0, 0]]

			elif used_for in ['demo']:
				return [self.U, 0.5, '규칙 없음']

		# -- 근거 조사

		n_s = (s_, 'object')
		n_o = (o_, 'object')

		# --

		self.R_M.construct_graph(n_s, n_o, NEC=True, LC=True)

		# --

		p_evidence = []

		if self.evidence_type in ['P', 'PN']:
			try:
				for r, w, g_cover, v_cover, a, b, c, d in sorted(self.R_P[p_], key=lambda x: x[1]):
					w = self.a * (1.0 - g_cover) + self.b * v_cover

					# --

					w = 1.0 - max((g_cover - (1.0 / self.c) * v_cover) / g_cover, self.min_penalty) * (1.0 - w)

					# --

					if a <= self.min_cover:
						w = 1.0 - self.min_penalty * (1.0 - w)

					# --

					binding = self.R_M.get_binding(n_s, n_o, r)

					# --

					if binding:
						r_inst = []

						# --

						for v_a, v_b, p, d in r:
							n_a = binding[v_a]
							n_b = binding[v_b]

							# --

							r_inst.append([RDF.remove_prefix(n_a[0]), RDF.remove_prefix(n_b[0]), p, d])

						# --

						p_evidence.append([r, r_inst, w])

			except:
				pass

			# --

			p_evidence = sorted(p_evidence, key=lambda x: x[2])

		# --

		n_evidence = []

		if self.evidence_type in ['N', 'PN']:
			try:
				for r, w, g_cover, v_cover, a, b, c, d in sorted(self.R_N[p_], key=lambda x: x[1]):
					w = self.a * (1.0 - g_cover) + self.b * v_cover

					# --

					w = 1.0 - max((g_cover - (1.0 / self.c) * v_cover) / g_cover, self.min_penalty) * (1.0 - w)

					# --

					if a <= self.min_cover * 2:
						w = 1.0 - self.min_penalty * (1.0 - w)

					# --

					binding = self.R_M.get_binding(n_s, n_o, r)

					# --

					if binding:
						r_inst = []

						# --

						for v_a, v_b, p, d in r:
							n_a = binding[v_a]
							n_b = binding[v_b]

							# --

							r_inst.append([RDF.remove_prefix(n_a[0]), RDF.remove_prefix(n_b[0]), p, d])

						# --

						n_evidence.append([r, r_inst, w])

			except:
				pass

			# --

			n_evidence = sorted(n_evidence, key=lambda x: x[2])

		# --

		try:
			r_p = p_evidence[0][0]
			i_p = p_evidence[0][1]
			w_p = p_evidence[0][2]

		except:
			r_p = []
			i_p = []
			w_p = 1.0

		# --

		try:
			r_n = n_evidence[0][0]
			i_n = n_evidence[0][1]
			w_n = n_evidence[0][2]

		except:
			r_n = []
			i_n = []
			w_n = 1.0

		# --

		s_p = self.score_A(w_p)
		s_n = self.score_A(w_n)

		# --

		if len(p_evidence) > 0:
			score = self.score_B(s_p, 0.0)

		elif len(n_evidence) > 0:
			score = self.score_B(0.0, s_n)

		else:
			score = self.score_B(0.0, 0.0)

		# --

		if used_for in ['eval']:
			if len(p_evidence) > 0:
				return [self.T, score, [self.R_M.simplify(r_p, 'P'), s_p, s_n, len(p_evidence), len(n_evidence)]]

			# --

			elif len(n_evidence) > 0:
				return [self.F, score, [self.R_M.simplify(r_n, 'N'), s_p, s_n, len(p_evidence), len(n_evidence)]]

			# --

			else:
				return [self.U, score, ['근거 없음', s_p, s_n, len(p_evidence), len(n_evidence)]]

		# --

		elif used_for in ['demo-wisekb']: # high recall for True
			if score >= self.score_threshold_A:
				return [self.T, score]
			
			else:
				return [self.F, score]

		# --

		elif used_for in ['demo-flagship']: # high recall for False
			if len(p_evidence) <= 0 and len(n_evidence) <= 0:
				return [self.U, 0.5, '근거 없음']

			elif s_p >= self.score_threshold_B:
				return [self.T, s_p, i_p]

			else:
				return [self.F, s_n, i_n]

		# --
		'''
		elif used_for in ['demo-flagship']:
			if len(p_evidence) > 0:
				return [self.T, score, i_p]

			# --

			elif len(n_evidence) > 0:
				return [self.F, score, i_n]

			# --

			else:
				return [self.F, score, '근거 없음']
		'''
		# --
		'''
		elif used_for in ['demo-flagship']: # high recall for False
			if len(p_evidence) <= 0 and len(n_evidence) <= 0:
				return [self.F, score, '근거 없음']

			elif score >= self.score_threshold_B:
				return [self.T, score, i_p]

			else:
				return [self.F, score, i_n]
		'''
	# --

	def score_A(self, w):
		return 1.0 - w

	# --

	def score_B(self, s_p, s_n):
		return (s_p - s_n + 1.0) / 2.0
		
# --

if __name__ == '__main__':
	main()