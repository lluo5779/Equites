from __future__ import print_function
import torch
import pandas as pd 
import numpy as np 
import util as ut

class TextClassDataLoader(object):

	def __init__(self, data, word_to_index = None, batch_size = 32):

		self.batch_size = batch_size
		#self.word_to_index = word_to_index

		#df = pd.read_csv(path_file)
		df = data
		#df['body'] = df['body'].apply(ut._tokenize)
		#df['body'] = df['body'].apply(self.generate_indexifyer())
		self.samples = df.values.tolist()

		self.n_samples = len(self.samples)
		self.n_batches = int(self.n_samples / self.batch_size)
		self.max_length = self._get_max_length()
		self._shuffle_indices()

		self.report()

	def _shuffle_indices(self):
		self.indices = np.random.permutations(self.n_samples)
		self.index = 0
		self.batch_index = 0

	def convert_targets(self, label):
		if label < self.mean_returns:
			label = 0
		else:
			label = 1

	def generate_indexifer(self):

		def indexify(lst_text):
			indices = []
			for word in lst_text:
				if word in self.word_to_index:
					indices.append(self.word_to_index[word])
				else:
					indices.append(self.word_to_index['__UNK__'])
			return indices
		return indexify


	@staticmethod
	def _padding(batch_x):
		batch_s = sorted(batch_x, key = lambda x: len(x))
		size = len(batch_s[-1])
		for i, x in enumerate(batch_x):
			missing = size - len(x)
			batch_x[i] = batch_x[i] + [0 for _ in range(missing)]
		return batch_x

	def _create_batch(self):
		batch = []
		n = 0
		while n < self.batch_size:
			_index = self.indices[self.index]
			batch.append(self.samples[_index])
			self.index += 1
			n += 1
		self.batch_index += 1

		label, string = tuple(zip(*batch))
		label = map(self.convert_targets(label))

		seq_lengths = torch.LongTensor(map(len, string))

		seq_tensor = torch.zeros((len(string), seq_lengths.max())).long()
		for idx, (seq, seqlen) in enumerate(zip(string, seq_lengths)):
			seq_tensor[idx, :seqlen] = torch.LongTensor(seq)

		seq_lengths, perm_idx = seq_lengths.sort(0, descending = True)
		seq_tensor = seq_tensor[perm_idx]
		# seq_tensor = seq_tensor.transpose(0, 1)
		label = torch.LongTensor(label)
		label = label[perm_idx]

		return seq_tensor, label, seq_lengths


	def __len__(self):
		return self.n_batches

	def __iter__(self):
		self._shuffle_indices()
		for i in range(self.n_batches):
			if self.batch_index == self.n_batches:
				raise StopIteration()
			yield self._create_batch()

	def show_samples(self, n = 10):
		for sample in self.samples[:n]:
			print(sample)

	def report(self):
		print('# samples: {}'.format(len(self.samples)))
		print('max len: {}'.format(self.max_length))
		print('# vocab: {}'.format(len(self.word_to_index)))
		print('# batches: {} (batch_size = {})'.format(self.n_batches, self.batch_size))