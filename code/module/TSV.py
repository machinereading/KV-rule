class TSV:
	def read_dict(self, path, key_num=1, func=False):
		result = {}

		# --

		with open(path) as i_file:
			for line in i_file.readlines():
				line = line.strip()

				# --

				import re

				list_ = re.split('\t', line)

				# --

				if len(list_) == 2:
					key, value = list_

				elif len(list_) >= 3 and key_num == 1:
					key = list_[0]
					value = tuple(list_[1:])

				elif len(list_) >= 3 and len(list_) - key_num == 1:
					key = tuple(list_[0:key_num])
					value = list_[-1]

				else:
					key = tuple(list_[0:key_num])
					value = tuple(list_[key_num:])

				# --

				if func:
					result[key] = value

				else:
					try:
						result[key].add(value)

					except:
						result[key] = set([value])

		# --

		return result

	def read_list(self, path):
		result = []

		with open(path) as i_file:
			for line in i_file.readlines():
				line = line.strip()

				# --

				import re

				list_ = re.split('\t', line)

				if len(list_) >= 2:
					result.append(list_)

				elif len(list_) == 1:
					result.append(list_[0])

		return result