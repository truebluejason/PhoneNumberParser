import torch
import torch.nn as nn

from neural_net.rnn import Encoder

class Decoder(nn.Module):
    """
    Accept hidden layers as an argument <num_layer x batch_size x hidden_size> for each hidden and cell state.
    At every forward call, output probability vector of <batch_size x output_size>.

    input_size: N_LETTER
    hidden_size: Size of the hidden dimension
    output_size: N_LETTER
    """
    def __init__(self, input_size, hidden_size, output_size, num_layers=1):
        super(Decoder, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers

        # Initialize LSTM - Notice it does not accept output_size
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers)
        self.fc1 = nn.Linear(hidden_size, output_size)
        self.softmax = nn.LogSoftmax(dim=2)

    def forward(self, input, hidden):
        """
        Run LSTM through 1 time step

        SHAPE REQUIREMENT
        - input: <1 x batch_size x N_LETTER>
        - hidden: (<num_layer x batch_size x hidden_size>, <num_layer x batch_size x hidden_size>)
        - lstm_out: <1 x batch_size x N_LETTER>
        """
        # input = input.view(len(input), self.batch_size, -1)
        lstm_out, hidden = self.lstm(input, hidden)
        lstm_out = self.fc1(lstm_out)
        lstm_out = self.softmax(lstm_out)
        return lstm_out, hidden

"""
DATASET = [
    "my name is jason",
    "will you workkkk",
    "what is lifeeeee",
    "im not too suree",
    "please god damnn",
    "memorize thissss"
]
"""
CHARS = "abcdefghijklmnopqrstuvwxyz "

DATASET = ["abcdefghijklmno" + n for n in CHARS]


EPOCHS = 1000

def char_to_index(char: str) -> int:
    return CHARS.find(char)
def index_to_char(index: int) -> str:
    return CHARS[index]
def string_to_tensor(string: str) -> list:
    tensor = torch.zeros(16,1,27)
    for i,char in enumerate(string):
        tensor[i,0,char_to_index(char)] = 1
    return tensor
def tensor_to_string(tensor: list) -> str:
    result = ""
    for i in range(tensor.shape[0]):
        index = torch.nonzero(tensor[i,0]).item()
        result += index_to_char(index)
    return result

enc = Encoder(27,16)
dec = Decoder(27+1,16,27)

def train(x, criterion, enc_optim, dec_optim):
    enc_optim.zero_grad()
    dec_optim.zero_grad()

    loss = 0.
    x = string_to_tensor(x)
    enc_hidden = enc.blank_hidden_layer()
    for i in range(x.shape[0]):
        # RNN requires 3 dimensional inputs
        _, enc_hidden = enc(x[i].unsqueeze(0), enc_hidden)
    
    dec_input = torch.zeros(1,1,27+1)
    dec_input[0,0,-1] = 1.
    dec_hidden = enc_hidden
    for i in range(x.shape[0]):
        dec_probs, dec_hidden = dec(dec_input, dec_hidden)
        _, nonzero_indexes = x[i].topk(1)
        loss += criterion(dec_probs[0], nonzero_indexes[0])
        best_index = torch.argmax(dec_probs,dim=2).item()
        dec_input = torch.zeros(1,1,27+1)
        dec_input[0,0,best_index] = 1.
    
    loss.backward()
    enc_optim.step()
    dec_optim.step()
    return loss.item()

def test(x):
    x = string_to_tensor(x)
    result = ""
    enc_hidden = enc.blank_hidden_layer()
    for i in range(x.shape[0]):
        # RNN requires 3 dimensional inputs
        _, enc_hidden = enc(x[i].unsqueeze(0), enc_hidden)
    
    dec_input = torch.zeros(1,1,27+1)
    dec_input[0,0,-1] = 1.
    dec_hidden = enc_hidden
    for i in range(x.shape[0]):
        dec_probs, dec_hidden = dec(dec_input, dec_hidden)
        best_index = torch.argmax(dec_probs,dim=2).item()
        dec_input = torch.zeros(1,1,27+1)
        dec_input[0,0,best_index] = 1.
        result += index_to_char(best_index)
    return result


criterion = torch.nn.NLLLoss()
enc_optim = torch.optim.Adam(enc.parameters(),lr=0.001)
dec_optim = torch.optim.Adam(dec.parameters(),lr=0.001)

losses = []
print("TRAINING")
for i in range(EPOCHS):
    epoch_loss = 0
    for num in DATASET:
        epoch_loss += train(num,criterion,enc_optim,dec_optim)
    print(epoch_loss)
    losses.append(epoch_loss)

import matplotlib.pyplot as plt
plt.plot(losses)
plt.xlabel('epochs')
plt.ylabel('loss')
plt.show()

print("TESTING")
for num in DATASET:
    print(f"Input: {num}, Output: {test(num)}")
