import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence


class RNN(nn.Module):

	def __init__(self,
				 vocab_size,
				 embed_size,
				 output_dim,
				 rnn_model = 'GRU',
				 embedding_tensor = None,
				 padding_index = 0,
				 hidden_size = 64,
				 num_layers = 1,
				 batch_first = True)

	super(RNN, self).__init__()
	self.encoder = None
	if torch.is_tensor(embedding_tensor):
		self.encoder = nn.Embedding(vocab_size, embed_size, padding_idx = padding_index, _weight = embedding_tensor)
		self.encoder.weight.requires_grad = False
	else:
		self.encoder = nn.Embedding(vocab_size, embed_size, padding_idx = padding_index)

	self.drop_en = nn.Dropout(p = 0.6)

	if rnn_model == 'LSTM':
		self.rnn = nn.LSTM(input_size = embed_size, hidden_size = hidden_size,
						   num_layers = num_layers, dropout = 0.5,
						   batch_first = True, bidirectional = True)
	elif rnn_model == 'GRU':
		self.rnn = nn.GRU(input_size = embed_size, hidden_size = hidden_size,
						  num_layers = num_layers, dropout = 0.5,
						  batch_first = True, bidirectional = True)

	self.bn2 = nn.BatchNorm1d(hidden_size * 2)
	self.fc = nn.Linear(hidden_size*2, num_output)

def forward(self, x, seq_lengths):
	x_embed = self.encoder(x)
	x_embed = self.drop_en(x_embed)
	packed_input = pack_padded_sequence(x_embed, seq_lengths.cpu().numpy(), batch_first = True)

	packed_output, ht = self.rnn(packed_input, None)
	out_rnn, _ = pad_packed_sequence(packed_output, batch_first = True)

	row_indices = torch.arange(0, x.size(0)).long()
	col_indices = seq_lengths - 1
	if next(self.parameters()).is_cuda():
		row_indices = row_indices.cuda()
		col_indices = col_indices.cuda()
	if self.use_last:
		last_tensor = out_rnn[row_indices, col_indices, :]
	else:
		last_tensor = out_rnn[row_indices, :, :]
		last_tensor = torch.mean(last_tensor, dim = 1)

	fc_input = self.bn2(last_tensor)
	out = self.fc(fc_input)
	return out