class RDF:
	cache = {}

	# --

	def parse(self, path):
		result = []

		# --

		import re

		form = re.split('[.]', path)[-1]

		if form in ['nt', 'ttl']:
			with open(path) as i_file:
				for line in i_file.readlines():
					line = line.strip()

					# --

					if line[0] == '#':
						continue

					# --

					import re

					# --

					try:
						s, p, o = re.findall(r'^<(.+?)>\s+<(.+?)>\s+<(.+?)>\s+\.$', line)[0]

						result.append([s, p, o, 'object'])

					except:
						try:
							s, p, o, ot = re.findall(r'^<(.+?)>\s+<(.+?)>\s+"(.+?)"\^\^<(.+?)>\s+\.$', line)[0]

							result.append([s, p, o, ot])

						except:
							try:
								s, p, o = re.findall(r'^<(.+?)>\s+<(.+?)>\s+"(.+?)"@.+?\s+\.$', line)[0]

								result.append([s, p, o, 'string'])

							except:
								try:
									s, p, o = re.findall(r'^<(.+?)>\s+<(.+?)>\s+"(.+?)".*\s+\.$', line)[0]

									result.append([s, p, o, 'string'])

								except:
									pass

		# --

		return result

	def remove_prefix(self, uri):
		try:
			self.cache['remove_prefix']

		except:
			self.cache['remove_prefix'] = {}

		# --

		try:
			return self.cache['remove_prefix'][uri]

		except:
			pass

		# --

		try:
			prefix_set = set([
				'http://dbpedia.org/ontology/',
				'http://dbpedia.org/resource/',
				'http://dbpedia.org/property/',
				'http://ko.dbpedia.org/resource/',
				'http://ko.dbpedia.org/property/'
			])

			for prefix in prefix_set:
				result = uri.replace(prefix, '')

				if len(result) < len(uri):
					self.cache['remove_prefix'][uri] = result

					# --

					return result

			# --

			import re

			if uri[-1] not in ['/', '#']:
				result = re.split(r'[/#]', uri)[-1]

			else:
				match = re.findall(r'^(.+?)([/#]+)$', uri)

				result = re.split(r'[/#]', match[0][0])[-1] + match[0][1]	

		except:
			result = uri
			
		# --

		self.cache['remove_prefix'][uri] = result

		# --

		return result

	def parse_literal(self, value, type_): # for date, number
		try:
			return self.cache['parse_literal'][value, type_]

		except:
			pass

		# --

		result = None

		# --

		import re

		from datetime import datetime

		# --

		try:
			if self.remove_prefix(type_) in ['date', 'time', 'dateTime']:
				# -- date (positive year)

				if re.search(r'^[0-9]{4,}-[0-9]{2}-[0-9]{2}$', value):
					result = datetime.strptime(value, '%Y-%m-%d')

				# -- time (integer second)

				elif re.search(r'^[0-9]{2}:[0-9]{2}:[0-9]{2}$', value):
					result = datetime.strptime(value, '%H:%M:%S')

				# -- dateTime (positive year, integer second)

				elif re.search(r'^[0-9]{4,}-[0-9]{2}-[0-9]{2}[T][0-9]{2}:[0-9]{2}:[0-9]{2}$', value):
					result = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')

			elif self.remove_prefix(type_) in ['gYear', 'gMonth', 'gDay', 'gYearMonth', 'gMonthDay']:
				# -- gYear (positive year)

				if re.search(r'^[0-9]{4,}$', value):
					result = datetime.strptime(value, '%Y')

				# -- gMonth

				elif re.search(r'^--[0-9]{2}$', value):
					result = datetime.strptime(value, '--%m')

				# -- gDay

				elif re.search(r'^---[0-9]{2}$', value):
					result = datetime.strptime(value, '---%d')

				# -- gYearMonth (positive year)

				elif re.search(r'^[0-9]{4,}-[0-9]{2}$', value):
					result = datetime.strptime(value, '%Y-%m')

				# -- gMonthDay

				elif re.search(r'^--[0-9]{2}-[0-9]{2}$', value):
					result = datetime.strptime(value, '--%m-%d')

			else:
				# -- integer

				if re.search(r'^[+-]?[0-9]+$', value):
					result = int(value)

				# -- float, double

				elif re.search(r'^[+-]?[0-9]+([.][0-9]+?)?([E][0-9]+?)?([e]-[0-9]+?)?$', value):
					result = float(value)

		except:
			pass

		# --

		try:
			self.cache['parse_literal']

		except:
			self.cache['parse_literal'] = {}

		# --

		self.cache['parse_literal'][value, type_] = result

		# --

		return result