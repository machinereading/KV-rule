FW = 1
BW = -1

# --

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

	# --

	with open(conf_name) as i_file:
		import json

		# --

		conf = json.loads(i_file.read())

	# --

	output = conf['inter-output']

	inst_path = conf['inst-path-A']

	# --

	from module.TSV import TSV

	TSV = TSV()

	from module.RDF import RDF

	RDF = RDF()

	# -- 인스턴스

	inst_list = []

	for path in inst_path:
		inst_list.append(TSV.read_list(path))

	inst = merge_inst(inst_list)

	# --

	p2so = {}

	for s, p, o, ot in inst:
		if ot in ['object']:
			try:
				p2so[p, FW].add((s, o))

			except:
				p2so[p, FW] = set([(s, o)])

			# --

			try:
				p2so[p, BW].add((o, s))

			except:
				p2so[p, BW] = set([(o, s)])

	# --

	p2s2o = {}

	for p, d in p2so:
		p2s2o[p, d] = {}

		# --

		for s, o in p2so[p, d]:
			try:
				p2s2o[p, d][s].add(o)

			except:
				p2s2o[p, d][s] = set([o])

	# -- Functionality

	F = {}

	# --

	iter_num = 0

	for p, d in p2s2o:
		s_set = p2s2o[p, d].keys()

		# --

		for s in s_set:
			try:
				F[p, d] += 1.0 / len(p2s2o[p, d][s]) # 함수성

			except:
				F[p, d] = 1.0 / len(p2s2o[p, d][s])

		# --

		try:
			F[p, d] /= len(s_set) # 평균 함수성

		except:
			F[p, d] = 0.0

		# --

		if F[p, d] == 0.0:
			del F[p, d]

		# --

		if iter_num % 100 == 0:
			print('F', iter_num, len(p2s2o))

		iter_num += 1

	# --

	with open(output + '/F.tsv', 'w+') as o_file:
		for p, d in sorted(F):
			o_file.write('\t'.join([p, str(d), str(F[p, d])]) + '\n')

	with open(output + '/F-simple.tsv', 'w+') as o_file:
		for p, d in sorted(F):
			o_file.write('\t'.join([RDF.remove_prefix(p), str(d), str(F[p, d])]) + '\n')

	# -- Asymmetric Similarity: S(A, B) != S(B, A)

	S = {}

	# --

	iter_num = 0

	for p1, d1 in p2s2o:
		for p2, d2 in p2s2o:
			s_set_common = p2s2o[p1, d1].keys() & p2s2o[p2, d2].keys()

			# --

			for s in s_set_common:
				try:
					S[p1, d1, p2, d2] += len(p2s2o[p1, d1][s] & p2s2o[p2, d2][s]) / len(p2s2o[p1, d1][s]) # 비대칭 유사도

				except:
					S[p1, d1, p2, d2] = len(p2s2o[p1, d1][s] & p2s2o[p2, d2][s]) / len(p2s2o[p1, d1][s])

			# --

			try:
				S[p1, d1, p2, d2] /= len(s_set_common) # 평균 비대칭 유사도

			except:
				S[p1, d1, p2, d2] = 0.0

			# --

			if S[p1, d1, p2, d2] == 0.0:
				del S[p1, d1, p2, d2]

		# --

		if iter_num % 100 == 0:
			print('S', iter_num, len(p2s2o))

		iter_num += 1

	# --

	with open(output + '/S.tsv', 'w+') as o_file:
		for p1, d1, p2, d2 in sorted(S):
			o_file.write('\t'.join([p1, str(d1), p2, str(d2), str(S[p1, d1, p2, d2])]) + '\n')

	with open(output + '/S-simple.tsv', 'w+') as o_file:
		for p1, d1, p2, d2 in sorted(S):
			o_file.write('\t'.join([RDF.remove_prefix(p1), str(d1), RDF.remove_prefix(p2), str(d2), str(S[p1, d1, p2, d2])]) + '\n')

# --

def merge_inst(inst_list):
	merged_inst = []

	for inst in inst_list:
		merged_inst += inst

	return merged_inst

# --

if __name__ == '__main__':
	main()