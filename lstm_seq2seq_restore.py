'''Restore a character-level sequence to sequence model from disk and use it
to generate predictions.

This script loads the s2s.h5 model saved by lstm_seq2seq.py and generates
sequences from it.  It assumes that no changes have been made (for example:
latent_dim is unchanged, and the input data and model architecture are unchanged).

See lstm_seq2seq.py for more details on the model architecture and how
it is trained.
'''
from __future__ import print_function

from keras.models import Model, load_model
from keras.layers import Input
import numpy as np

batch_size = 64  # Batch size for training.
epochs = 1000  # Number of epochs to train for.
latent_dim = 256  # Latent dimensionality of the encoding space.
num_samples = 10000  # Number of samples to train on.
# Path to the data txt file on disk.
data_path = '/home/mustafa/Development/kerasTut/fra.txt'

# Vectorize the data.  We use the same approach as the training script.
# NOTE: the data must be identical, in order for the character -> integer
# mappings to be consistent.
# We omit encoding target_texts since they are not needed.
input_texts = []
target_texts = []
input_characters = set()
target_characters = set()
with open(data_path, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')
for line in lines[: min(num_samples, len(lines) - 1)]:
    input_text, target_text = line.split('\t')
    # We use "tab" as the "start sequence" character
    # for the targets, and "\n" as "end sequence" character.
    target_text = '\t' + target_text + '\n'
    input_texts.append(input_text)
    target_texts.append(target_text)
    for char in input_text:
        if char not in input_characters:
            input_characters.add(char)
    for char in target_text:
        if char not in target_characters:
            target_characters.add(char)


alphabet = ' abcdefghijklmnopqrstuvwxyzßMFN'
for char in alphabet:
    if char not in input_characters:
        input_characters.add(char)
for char in alphabet:
    if char not in target_characters:
        target_characters.add(char)
        
input_characters = sorted(list(input_characters))
target_characters = sorted(list(target_characters))
num_encoder_tokens = len(input_characters)
num_decoder_tokens = len(target_characters)
max_encoder_seq_length = max([len(txt) for txt in input_texts])
max_decoder_seq_length = max([len(txt) for txt in target_texts])

print('Number of samples:', len(input_texts))
print('Number of unique input tokens:', num_encoder_tokens)
print('Number of unique output tokens:', num_decoder_tokens)
print('Max sequence length for inputs:', max_encoder_seq_length)
print('Max sequence length for outputs:', max_decoder_seq_length)

input_token_index = dict(
    [(char, i) for i, char in enumerate(input_characters)])
target_token_index = dict(
    [(char, i) for i, char in enumerate(target_characters)])

encoder_input_data = np.zeros(
    (len(input_texts), max_encoder_seq_length, num_encoder_tokens),
    dtype=np.int)
for i, input_text in enumerate(input_texts):
    for t, char in enumerate(input_text):
        encoder_input_data[i, t, input_token_index[char]] = 1.

# Restore the model and construct the encoder and decoder.
model = load_model('s2s.h5')

encoder_inputs = model.input[0]   # input_1
encoder_outputs, state_h_enc, state_c_enc = model.layers[2].output   # lstm_1
encoder_states = [state_h_enc, state_c_enc]
encoder_model = Model(encoder_inputs, encoder_states)

decoder_inputs = model.input[1]   # input_2
decoder_state_input_h = Input(shape=(latent_dim,), name='input_3')
decoder_state_input_c = Input(shape=(latent_dim,), name='input_4')
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
decoder_lstm = model.layers[3]
decoder_outputs, state_h_dec, state_c_dec = decoder_lstm(
    decoder_inputs, initial_state=decoder_states_inputs)
decoder_states = [state_h_dec, state_c_dec]
decoder_dense = model.layers[4]
decoder_outputs = decoder_dense(decoder_outputs)
decoder_model = Model(
    [decoder_inputs] + decoder_states_inputs,
    [decoder_outputs] + decoder_states)

# Reverse-lookup token index to decode sequences back to
# something readable.
reverse_input_char_index = dict(
    (i, char) for char, i in input_token_index.items())
reverse_target_char_index = dict(
    (i, char) for char, i in target_token_index.items())


# Decodes an input sequence.  Future work should support beam search.
def decode_sequence(input_seq):
    # Encode the input as state vectors.
    states_value = encoder_model.predict(input_seq)

    # Generate empty target sequence of length 1.
    target_seq = np.zeros((1, 1, num_decoder_tokens))
    # Populate the first character of target sequence with the start character.
    target_seq[0, 0, target_token_index['\t']] = 1.

    # Sampling loop for a batch of sequences
    # (to simplify, here we assume a batch of size 1).
    stop_condition = False
    decoded_sentence = ''
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict(
            [target_seq] + states_value)

        # Sample a token
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        sampled_char = reverse_target_char_index[sampled_token_index]
        decoded_sentence += sampled_char

        # Exit condition: either hit max length
        # or find stop character.
        if (sampled_char == '\n' or
           len(decoded_sentence) > max_decoder_seq_length):
            stop_condition = True

        # Update the target sequence (of length 1).
        target_seq = np.zeros((1, 1, num_decoder_tokens))
        target_seq[0, 0, sampled_token_index] = 1.

        # Update states
        states_value = [h, c]

    return decoded_sentence


np.set_printoptions(threshold=np.inf)
for seq_index in range(len(input_texts)):
    # Take one sequence (part of the training set)
    # for trying out decoding.
    input_seq = encoder_input_data[seq_index: seq_index + 1]
    decoded_sentence = decode_sequence(input_seq)
    print('-')
    print('Input sentence:', input_texts[seq_index])
    print('Decoded sentence:', decoded_sentence)
    

#EIGENER ANSATZ
"""
input_charTEST = set()

textTEST = ['fahr mich mal in die F']
alphabet = ' abcdefghijklmnopqrstuvwxyzßMFN'

for char in alphabet:
    if char not in input_charTEST:
        input_charTEST.add(char)

input_charTEST = sorted(list(input_charTEST))
print(input_charTEST)

input_token_index_TEST = dict(
    [(char, i) for i, char in enumerate(input_charTEST)])

encoderTEST = np.zeros((len(textTEST), 42, len(alphabet)), dtype=np.int)

for i, text in enumerate(textTEST):
    for t, char in enumerate(text):
        encoderTEST[i, t, input_token_index[char]] = 1

print(encoderTEST[0:1])
input_seq = encoderTEST[0:1]
decoded_sentence = decode_sequence(input_seq)
print(decoded_sentence)
"""

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

userInput = "ich will jetzt in die hufelandstraße"

datenDict = {"marienplatz":"M", "straße":"F", "dorf":"N", "hufelandstraße":"F", "allianzarena" : "F", "ingolstadt" : "N"}

#textTEST = ' '.join([datenDict.get(i, i) for i in userInput.split()])
data = userInput.split()
replacedWord = ''
for i, j in enumerate(data):
    if j in datenDict:
        replacedWord = data[i]
        data[i]= datenDict[j]

textTEST = " ".join(data)
print(textTEST) #ich will zur F
print(replacedWord) #straße

input_charTEST = set()
alphabet = ' abcdefghijklmnopqrstuvwxyzßMFN'

for char in alphabet:
    if char not in input_charTEST:
        input_charTEST.add(char)

input_charTEST = sorted(list(input_charTEST))
input_token_index_TEST = dict(
    [(char, i) for i, char in enumerate(input_charTEST)])

encoderTEST = np.zeros((1, 42, len(alphabet)), dtype=np.int)

for t, char in enumerate(textTEST):
    encoderTEST[0, t, input_token_index[char]] = 1

input_seq = encoderTEST
decoded_sentence = decode_sequence(input_seq)

#import re
#decoded_sentence = re.sub("N", replacedWord, decoded_sentence)
decoded_sentence = decoded_sentence.replace("N", replacedWord)
decoded_sentence = decoded_sentence.replace("M", replacedWord)
decoded_sentence = decoded_sentence.replace("F", replacedWord)

print("Benutzereingabe:", userInput)
print("Systemausgabe:", decoded_sentence)


"""
#erster Ansatz

input_charTEST = set()

textTEST = ['stop', 'wir muessen schleunigst nach hause']
alphabet = ' abcdefghijklmnopqrstuvwxyzßMFN'

for char in alphabet:
    if char not in input_charTEST:
        input_charTEST.add(char)

input_charTEST = sorted(list(input_charTEST))
print(input_charTEST)

input_token_index_TEST = dict(
    [(char, i) for i, char in enumerate(input_charTEST)])

encoderTEST = np.zeros((len(textTEST), 42, len(alphabet)), dtype=np.int)

for i, text in enumerate(textTEST):
    for t, char in enumerate(text):
        encoderTEST[i, t, input_token_index[char]] = 1

print(encoderTEST[1:2])
input_seq = encoderTEST[1:2]
decoded_sentence = decode_sequence(input_seq)
print(decoded_sentence)
"""
