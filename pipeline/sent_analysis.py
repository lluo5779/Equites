import time
import gc
import os

import numpy as np 
from sklearn.externals import joblib
import torch
from torch import nn
import torch.backends.cudnn as cudnn

from vocab import VocabBuilder, GloveVocabBuilder
from dataloader import TextClassDataLoader
from model import RNN
from util import AverageMeter, accuracy
from util import adjust_learning_rate

np.random.seed(0)
torch.manual_seed(0)

class SentimentAnalysis(object):

	def __init__(self,
				 epochs = 50,
				 batch_size = 128,
				 learning_rate = 0.005,
				 weight_decay = 1e-4,
				 print_freq = 10,
				 save_freq = 10,
				 embedding_size = 50,
				 hidden_size = 128,
				 layers = 2,
				 view_size = None,
				 min_samples = 5,
				 cuda = 5,
				 glove = None,
				 rnn = 'GRU',
				 mean_seq = False,
				 clip = 0.25):
		self.epochs = epochs
		self.batch_size = batch_size
		self.lr = learning_rate
		self.wd = weight_decay
		self.pf = print_freq
		self.sf = save_freq
		self.embedding_size = embedding_size
		self.hid_size = hidden_size
		self.layers = layers
		self.view_size = view_size
		self.min_samples = min_samples
		self.cuda = cuda
		self.glove = glove
		self.rnn  = rnn
		self.mean_seq = mean_seq
		self.clip = clip
		self.model = None

	def get_vocab(self):
		print("Creating vocabulary...")

		if os.path.exists(self.glove):
			v_builder = GloveVocabBuilder(path_glove = self.glove)
			d_word_index, embed = v_builder.get_word_index()
			self.embedding_size = embed.size(1)
		else:
			v_builder = VocabBuilder(path_file = '../data/train.csv')
			d_word_index, embed = v_builder.get_word_index(min_samples = self.min_samples)

		if not os.path.exists('../data/gen'):
			os.mkdir('../data/gen')
		joblib.dump(d_word_index, '../data/gen/d_word_index.pkl', compress = 3)
		return d_word_index, embed

	def get_trainer(self, d_word_index):
		print('Creating dataloaders...')
		train_loader = TextClassDataLoader('../data/train.csv', d_word_index, batch_size = self.batch_size)
		val_loader = TextClassDataLoader('../data/test.csv', d_word_index, batch_size = self.batch_size)
		return train_loader, val_loader

	def get_model(self, d_word_index, embed):
		print("Creating RNN model...")
		vocab_size = len(d_word_index)
		self.model = RNN(vocab_size = vocab_size, embed_size = self.embedding_size,
						 num_outputs = self.view_size, rnn_model = self.rnn,
						 use_last = (not self.mean_seq), hidden_size = self.hid_size,
						 embedding_tensor = embed, num_layers = self.layers, batch_first = True)
		print(model)

		optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr = self.lr, weight_decay = self.wd)
		criterion = 'SOMETHING AIDAN YOU SILLY' #BCE LOSS, SET target = 1 if greater than median returns, look at prices/prices.shift(1) returns stuff

		print(optimizer)
		print(criterion)

		if self.cuda:
			torch.backends.cudnn.enabled = True
			cudnn.benchmark = True
			model.cuad()
			criterion = criterion.cuda() #MAYBE THIS IS IMPOSSIBLE

		return model, criterion, optimizer

def train(train_loader, model, criterion, optimizer, epoch, cuda):
	batch_time = AverageMeter()
	data_time = AverageMeter()
	losses = AverageMeter()
	top1 = AverageMeter()

	model.train()

	end = time.time()
	for i, (input, target, seq_lengths) in enumerate(train_loader):
		data_time.update(time.time() - end)

		if cuda:
			input = input.cuda(async = True)
			target = target.cuda(async = True)

		output = model(input, seq_lengths)
		loss = criterion(output, target)

		prec1 = accuracy(output.data, target, topk = (1,))
		losses.update(loss.data, input.size(0))
		top1.update(prec1[0][0], input.size(0))

		optimizer.zero_grad()
		loss.backward()

		torch.nn.utils.clip_grad_norm_(model.parameters(), self.clip)
		optimizer.step()

		batch_time.update(time.time() - end)
		end = time.time()
		
		if i != 0 and i % args.print_freq == 0:
			print('Epoch: [{0}][{1}/{2}]  Time {batch_time.val:.3f} ({batch_time.avg:.3f})  '
				  'Data {data_time.val:.3f} ({data_time.avg:.3f})  Loss {loss.val:.4f} ({loss.avg:.4f})  '
				  'Prec@1 {top1.val:.3f} ({top1.avg:.3f})'.format(
				   epoch, i, len(train_loader), batch_time=batch_time, data_time=data_time, loss=losses, top1=top1))
			gc.collect()

def test(val_loader, model, criterion, cuda):
	batch_time = AverageMeter()
	losses = AverageMeter()
	top1 = AverageMeter()

	model.eval()
	end = time.time()
	for i, (input, target, seq_lengths) in enumerate(val_loader):

		if cuda:
			input = input.cuda(async = True)
			target = target.cuda(async = True)

		output = model(input, seq_lengths)
		loss = criterion(output, target)

		prec1 = accuracy(output.data, target, topk = (1,))
		losses.update(loss.data, input.size(0))
		top1.update(prec1[0][0], input.size(0))

		batch_time.update(time.time() - end)
		end = time.time()

		if i!= 0 and i % args.print_freq == 0:
			print('Test: [{0}/{1}]  Time {batch_time.val:.3f} ({batch_time.avg:.3f})  '
				  'Loss {loss.val:.4f} ({loss.avg:.4f})  Prec@1 {top1.val:.3f} ({top1.avg:.3f})'.format(
				   i, len(val_loader), batch_time=batch_time, loss=losses, top1=top1))
			gc.collect()

	print(' * Prec@1 {top1.avg:.3f}'.format(top1 = top1))
	return top1.avg


def main():
	sent_analysis = SentimentAnalysis()
	d_word_index, embed = sent_analysis.get_vocab()
	train_loader, val_loader = sent_analysis.get_trainer(d_word_index)
	model, criterion, optimizer = sent_analysis.get_model(d_word_index, embed)

	print(sent_analysis.epochs())
	for epoch in range(1, sent_analysis.epochs() + 1):

		adjust_learning_rate(sent_analysis.lr(), optimizer, epoch)
		train(train_loader, model, criterion, optimizer, epoch)
		test(val_loader, model, criterion)

		if epoch % sent_analysis.save_freq() == 0:
			name_model = 'rnn_{}.pkl'.format(epoch)
			path_save_model = os.path.join('../data/gen', name_model)
			joblib.dump(model.float(), path_save_model, compress = 2)