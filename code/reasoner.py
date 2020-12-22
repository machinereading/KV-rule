def main():
	import argparse

	parser = argparse.ArgumentParser()

	parser.add_argument('-cn')

	args = parser.parse_args()

	# --

	conf_name = args.cn

	print(conf_name)
	
	# --

	with open(conf_name) as i_file:
		import json

		# --

		conf = json.loads(i_file.read())

	# --

	import filter as filter_
	
	rf = filter_.RF(conf)

	# --

	rr = RR(conf, rf)

	# --

	rr.reason_object('박지성', 'team')

	#rr.reason_object('레오나르도_다_빈치', 'knownFor')

	#rr.reason_object('레오나르도_다_빈치', 'notableWork')

	#rr.reason_object('로마', 'country')

# --

class RR:
	def __init__(self, conf, rf=None):
		o_r_path = conf['o-r-path']
		i_r_path = conf['i-r-path']

		# --

		rank_threshold = conf['rank-threshold']

		# --

		self.max_distance = conf['max-distance-B']

		# --

		self.score_threshold = conf['score-threshold-B']

		# --

		type_dr_path = conf['type-dr-path']

		# --

		self.r_prefix = conf['r-prefix']
		self.o_prefix = conf['o-prefix']

		# --

		from module.TSV import TSV

		TSV = TSV()

		# --

		self.o_r = TSV.read_dict(o_r_path, func=True)

		# --

		self.i_r = {}

		for p, d, r, rank in TSV.read_list(i_r_path):
			if rank_threshold:
				if int(rank) <= rank_threshold:
					try:
						self.i_r[p].add(r)

					except:
						self.i_r[p] = set([r])

		# --

		if rf:
			self.rf = rf

		else:
			import filter as filter_

			self.rf = filter_.RF(conf)

		# --

		self.type_ = self.rf.R_M.type_

		self.type_dr = TSV.read_dict(type_dr_path)

		# --

		self.e2e = {}

		self.sp2o = {}

		for s, p, o, ot in self.rf.R_M.inst:
			if ot in ['object']:
				if s == o:
					continue

				# --

				try:
					self.e2e[s].add(o)

				except:
					self.e2e[s] = set([o])

				# --

				try:
					self.e2e[o].add(s)

				except:
					self.e2e[o] = set([s])

				# --

				try:
					self.sp2o[s, p].add(o)

				except:
					self.sp2o[s, p] = set([o])

	# --

	def reason_object(self, s, p):
		if 'http://' not in s:
			s_ = self.r_prefix + s

		else:
			s_ = s

		if 'http://' not in p:
			p_ = self.o_prefix + p

		else:
			p_ = p

		print(s_, p_)

		# --

		o_set = self.generate_object(s_, p_)

		print(o_set)

		# --

		if len(o_set) <= 0:
			return None

		# --

		score_list = []

		for o in o_set:
			label, score, expl = self.rf.validate(s_, p_, o)

			# --

			score_list.append([o, score])

		# --

		score_list = sorted(score_list, key=lambda x: x[1], reverse=True)

		print(score_list)

		# --

		max_score = score_list[0][1]

		# --

		result = []

		for o, score in score_list:
			if score >= self.score_threshold:
				result.append([o, score])

		print(result)

		# --

		if len(result) <= 0:
			return None

		# --

		return result

	# --

	def generate_object(self, s, p):
		o_t_set = set([])

		# --

		try:
			o_t_set.add(self.o_r[p])

		except:
			try:
				o_t_set |= self.i_r[p]

			except:
				pass

		# --

		o_set = set([])

		# --

		curr_set = set([s])
		next_set = set([])
		done_set = set([])

		for i in range(self.max_distance):
			for n in curr_set - done_set:
				for m in self.e2e[n]:
					m_t_set = set([])

					try:
						m_t_set |= self.type_[m]

					except:
						try:
							m_t_set |= self.type_dr[m]

						except:
							pass

					# --

					if len(m_t_set & o_t_set) >= 1:
						o_set.add(m)

				# --

				next_set |= self.e2e[n]

			# --

			done_set |= curr_set

			# --

			curr_set = next_set
			next_set = set([])

		# --

		try:
			o_set |= self.sp2o[s, p]

		except:
			pass

		# --

		return o_set

# --

if __name__ == '__main__':
	main()