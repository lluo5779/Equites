import csv

class AverageMeter(object):

	def __init__(self):
		self.reset()

	def reset(self):
		self.val = 0
		self.avg = 0
		self.sum = 0
		self.count = 0

	def update(self, val, n = 1):
		self.val = val
		self.sum += val * n
		self.count += n
		self.avg = self.sum/self.count

	def accuracy(output, target, topk(1,)):
		maxk = max(topk)
		batch_size = target.size(0)

		_, pred = output.topk(maxk, 1, Tru, True)
		pred = pred.t()
		correct = pred.eq(targe.view(1, -1).expand_as(pred))

		res = []
		for k in topk:
			correct_k = correct[:k].view(-1).float().sum(0, keepdim = True)
			res.append(correct_k.mul_(100.0 / batch_size))
		return res

	def adjust_learning_rate(lr, optimizer, epoch):
		lr = lr * (0.1 ** (epoch // 8))
		for param_group in optimizer.param_groups:
			param_group['lr'] = lr