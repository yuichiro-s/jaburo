from django.conf import settings

import numpy as np
import chainer
import chainer.links as L
import chainer.functions as F
from chainer import Variable

import uuid


class Rnnlm(chainer.Chain):

    def __init__(self, n_vocab, n_units, train=True):
        super(Rnnlm, self).__init__(
            embed=L.EmbedID(n_vocab, n_units),
            l1=L.LSTM(n_units, n_units),
            l2=L.LSTM(n_units, n_units),
            l3=L.Linear(n_units, n_vocab),
        )
        for param in self.params():
            param.data[...] = np.random.uniform(-0.1, 0.1, param.data.shape)
        self.train = train

    def reset_state(self):
        self.l1.reset_state()
        self.l2.reset_state()

    def __call__(self, x):
        h0 = self.embed(x)
        h1 = self.l1(F.dropout(h0, train=self.train))
        h2 = self.l2(F.dropout(h1, train=self.train))
        y = self.l3(F.dropout(h2, train=self.train))
        return y


def lookup_vocab(toks):
    return list(map(lambda tok: settings.VOCAB.get(tok.lower(), 0), toks))


def score(toks, top_num=10):
    model = settings.LM
    model.predictor.reset_state()
    ids = lookup_vocab(toks)
    lst = []
    my_id = uuid.uuid4()
    settings.LM_LOCK = my_id
    #print(list(zip(ids, toks)))
    for i, tok_id in enumerate(ids[:-1]):
        if settings.LM_LOCK != my_id:
            raise Exception('Interrupted')
        arr = np.asarray([tok_id], np.int32)
        v = Variable(arr)
        prob = F.softmax(model.predictor(v)).data[0].astype(np.float64)
        next_id = ids[i+1]
        next_prob = prob[next_id]
        id_probs = sorted(enumerate(prob), key=lambda ts: -ts[1])
        w_probs = []
        for id, p in id_probs[:top_num]:
            w_probs.append((settings.VOCAB_REV[id], float(p)))
        lst.append((next_prob, w_probs))
    return lst


def generate(init_toks, random=False, temp=3.0, max_len=200):
    model = settings.LM
    model.predictor.reset_state()
    init_ids = lookup_vocab(init_toks)
    lst = []
    v = None
    my_id = uuid.uuid4()
    settings.LM_LOCK = my_id
    for i, tok_id in enumerate(init_ids):
        if settings.LM_LOCK != my_id:
            raise Exception('Interrupted')
        arr = np.asarray([tok_id], np.int32)
        v = Variable(arr)
        if i < len(init_ids) - 1:
            model.predictor(v)

    for i in range(max_len):
        prob = F.softmax(model.predictor(v)).data[0].astype(np.float64)
        prob[0] = 0 # no <UNK>
        prob **= temp
        if random:
            prob /= np.sum(prob)
            next_id = np.random.choice(range(len(prob)), p=prob)
        else:
            next_id = np.argmax(prob)
        w = settings.VOCAB_REV[next_id]
        if w == '__t__':
            break
        else:
            lst.append(w)
            arr = np.asarray([next_id], np.int32)
            v = Variable(arr)

    return lst
