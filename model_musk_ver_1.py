# coding=utf-8
# @author: cer
import tensorflow as tf
from tensorflow.contrib import layers
import numpy as np
from tensorflow.contrib.rnn import LSTMCell, LSTMStateTuple, MultiRNNCell
import sys
import random

class Model_musk:
    def __init__(self, input_steps, embedding_size, hidden_size, vocab_size, slot_size,
                 intent_size, epoch_num, batch_size=16, n_layers=1):
        self.input_steps = input_steps
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size
        self.n_layers = n_layers
        self.batch_size = batch_size
        self.vocab_size = vocab_size
        self.slot_size = slot_size
        self.intent_size = intent_size
        self.epoch_num = epoch_num
        self.prediction_confidence = 0
        self.word_size = 4819
        self.hidden_embedding_size = 64
        #self.encoder_inputs = tf.placeholder(tf.int32, [input_steps, batch_size],
        #                                     name='encoder_inputs')

        # 每句输入的实际长度，除了padding
        self.encoder_inputs_actual_length = tf.placeholder(tf.int32, [batch_size],
                                                           name='encoder_inputs_actual_length')
        self.decoder_targets = tf.placeholder(tf.int32, [batch_size, input_steps],
                                              name='decoder_targets')
        self.intent_targets = tf.placeholder(tf.int32, [batch_size],
                                             name='intent_targets')
        self.embedding_npy_musk = tf.placeholder(tf.float32, [input_steps, batch_size, self.word_size])

    def build(self):

        # load numpy
        #embed_npy_musk = np.load( 'embedding.npy' )
        # train = 1
        # if train:
        #     embed_npy = np.load('embeddings_5491_6491.npy')
        #
        #     word2index_file = open( 'word2index_calibrated.txt', 'r' )
        #     expend_size = len( word2index_file.readlines() ) - len( embed_npy )
        #     word2index_file.close()
        #     if(expend_size>0):
        #         embed_expend = np.random.random((expend_size,self.embedding_size))
        #         embed_npy_musk = np.concatenate([embed_npy, embed_expend])
        #         del embed_expend, embed_npy
        #         np.save("embed_npy_musk_5491_6491.npy", embed_npy_musk)
        #     else:
        #         embed_npy_musk = embed_npy
        #         del embed_npy
        # else:

        self.embeddings = self.embedding_npy_musk
        self.weight = tf.Variable( tf.random_uniform([self.word_size, self.hidden_embedding_size],-0.1,0.1 ) ,dtype=tf.float32)
        self.bias = tf.Variable( tf.random_uniform( [self.hidden_embedding_size],-0.1,0.1 ) ,dtype=tf.float32)
        self.actual_embedding = tf.einsum( 'aij,jk->aik', self.embeddings, self.weight )
        self.encoder_inputs_embedded = tf.add( self.actual_embedding, self.bias )
        #self.actual_embedding = tf.add( tf.matmul( self.embeddings[1], self.weight ), self.bias )
        #self.encoder_inputs_embedded = tf.nn.embedding_lookup( self.actual_embedding, self.encoder_inputs )
        # 50 * 16 * 64
        self.slot_embedding = tf.Variable(tf.random_uniform([self.slot_size,self.hidden_embedding_size]))

        #embed_npy_musk = np.load( 'embeddings_5491_6491.npy' )
        #self.embeddings = tf.Variable( embed_npy_musk, dtype=tf.float32, name="embedding" )
        #self.encoder_inputs_embedded = tf.nn.embedding_lookup(self.embeddings, self.encoder_inputs)

        # Encoder

        # 使用单个LSTM cell
        encoder_f_cell = LSTMCell(self.hidden_size)
        encoder_b_cell = LSTMCell(self.hidden_size)
        # encoder_inputs_time_major = tf.transpose(self.encoder_inputs_embedded, perm=[1, 0, 2])
        # 下面四个变量的尺寸：T*B*D，T*B*D，B*D，B*D
        # (encoder_fw_outputs, encoder_bw_outputs), (encoder_fw_final_state, encoder_bw_final_state) = \
        #     tf.nn.bidirectional_dynamic_rnn(cell_fw=encoder_f_cell,
        #                                     cell_bw=encoder_b_cell,
        #                                     inputs=self.encoder_inputs_embedded,
        #                                     sequence_length=self.encoder_inputs_actual_length,
        #                                     dtype=tf.float32, time_major=True)

        # ======== Musk multi-layer LSTM ===========
        #input = self.encoder_inputs_embedded
        #for i in range(0,self.n_layers):

        #encoder_f_mlstm_cell = MultiRNNCell( [encoder_f_cell] * self.n_layers, state_is_tuple=True )
        #encoder_b_mlstm_cell = MultiRNNCell( [encoder_b_cell] * self.n_layers, state_is_tuple=True )
        #print(encoder_f_cell)
        # encoder_inputs_time_major = tf.transpose(self.encoder_inputs_embedded, perm=[1, 0, 2])
        # 下面四个变量的尺寸：T*B*D，T*B*D，B*D，B*D
        (encoder_fw_outputs, encoder_bw_outputs), (encoder_fw_final_state, encoder_bw_final_state) = \
            tf.nn.bidirectional_dynamic_rnn( cell_fw=encoder_f_cell,
                                             cell_bw=encoder_b_cell,
                                             inputs=self.encoder_inputs_embedded,
                                             sequence_length=self.encoder_inputs_actual_length,
                                             dtype=tf.float32, time_major=True, scope="BLSTM_1")

        # input = tf.concat( (encoder_fw_outputs, encoder_bw_outputs), 2 )
        #
        # hidden1_f_cell = LSTMCell( self.hidden_size )
        # hidden1_b_cell = LSTMCell( self.hidden_size )
        # (encoder_fw_outputs, encoder_bw_outputs), (encoder_fw_final_state, encoder_bw_final_state) = \
        #    tf.nn.bidirectional_dynamic_rnn( cell_fw=hidden1_f_cell,
        #                                     cell_bw=hidden1_b_cell,
        #                                     inputs=self.encoder_inputs_embedded,
        #                                     sequence_length=self.encoder_inputs_actual_length,
        #                                     dtype=tf.float32, time_major=True, scope="BLSTM_2")

        encoder_outputs = tf.concat((encoder_fw_outputs, encoder_bw_outputs), 2)

        encoder_final_state_c = tf.concat(
            (encoder_fw_final_state.c, encoder_bw_final_state.c), 1)

        encoder_final_state_h = tf.concat(
            (encoder_fw_final_state.h, encoder_bw_final_state.h), 1)

        self.encoder_final_state = LSTMStateTuple(
            c=encoder_final_state_c,
            h=encoder_final_state_h
        )
        print("encoder_outputs: ", encoder_outputs)
        print("encoder_outputs[0]: ", encoder_outputs[0])
        print("encoder_final_state_c: ", encoder_final_state_c)

        # Decoder
        decoder_lengths = self.encoder_inputs_actual_length
        self.slot_W = tf.Variable(tf.random_uniform([self.hidden_size * 2, self.slot_size], -1, 1),
                             dtype=tf.float32, name="slot_W")
        self.slot_b = tf.Variable(tf.zeros([self.slot_size]), dtype=tf.float32, name="slot_b")
        intent_W = tf.Variable(tf.random_uniform([self.hidden_size * 2, self.intent_size], -0.1, 0.1),
                               dtype=tf.float32, name="intent_W")
        intent_b = tf.Variable(tf.zeros([self.intent_size]), dtype=tf.float32, name="intent_b")

        # 求intent
        intent_logits = tf.add(tf.matmul(encoder_final_state_h, intent_W), intent_b)
        # intent_prob = tf.nn.softmax(intent_logits)
        self.intent = tf.argmax(intent_logits, axis=1)

        #JerryB +++
        #intent_prediction = tf.equal(tf.argmax(intent_logits,1), tf.argmax(tf.one_hot(self.intent_targets, depth=self.intent_size, dtype=tf.float32),1))
        #intent_prediction = tf.equal(tf.argmax(intent_logits,1), tf.argmax(self.intent_targets,1))
        intent_prob = tf.nn.softmax(intent_logits)
        #self.accuracy = intent_prob[0][12]
        max_index = tf.argmax(intent_prob,1)[0]
        self.accuracy = intent_prob[0][max_index]
        #self.accuracy = tf.argmax(intent_logits,1)
        #self.accuracy = tf.reduce_mean(tf.cast(intent_logits, tf.float32))
        #JerryB ---

        sos_time_slice = tf.zeros( [self.batch_size], dtype=tf.int32, name='SOS' )
        #sos_time_slice = tf.ones( [self.batch_size], dtype=tf.int32, name='SOS' ) * 2
        sos_step_embedded = tf.nn.embedding_lookup(self.encoder_inputs_embedded[0], sos_time_slice)
        # pad_time_slice = tf.zeros([self.batch_size], dtype=tf.int32, name='PAD')
        # pad_step_embedded = tf.nn.embedding_lookup(self.embeddings, pad_time_slice)
        pad_step_embedded = tf.zeros([self.batch_size, self.hidden_size*2+self.hidden_embedding_size],
                                     dtype=tf.float32)

        def initial_fn():
            initial_elements_finished = (0 >= decoder_lengths)  # all False at the initial step
            initial_input = tf.concat((sos_step_embedded, encoder_outputs[0]), 1)
            return initial_elements_finished, initial_input

        def sample_fn(time, outputs, state):
            # 选择logit最大的下标作为sample
            print("outputs", outputs)
            #output_logits = tf.add(tf.matmul(outputs, self.slot_W), self.slot_b)
            #print("slot output_logits: ", output_logits)
            #prediction_id = tf.argmax(output_logits, axis=1)
            prediction_id = tf.to_int32( tf.argmax( outputs, axis=1 ) )

            #output = tf.Print( outputs, [outputs], message="This is output: " )

            # Musk +++
            #prediction_ids = outputs
            #prediction_prob = tf.nn.softmax(outputs)
            #prediction_index = tf.argmax( outputs, 1 )[0]
            #self.prediction_confidence = prediction_prob[0][prediction_index]
            # Musk ---
            return prediction_id

        def next_inputs_fn(time, outputs, state, sample_ids):
            # 上一个时间节点上的输出类别，获取embedding再作为下一个时间节点的输入

            # Musk_embedding +++
            # pred_embedding = tf.nn.embedding_lookup( self.embeddings, sample_ids )
            pred_embedding = tf.nn.embedding_lookup( self.slot_embedding, sample_ids )
            # Musk_embedding ---

            # 输入是h_i+o_{i-1}+c_i
            next_input = tf.concat((pred_embedding, encoder_outputs[time]), 1)
            elements_finished = (time >= decoder_lengths)  # this operation produces boolean tensor of [batch_size]
            all_finished = tf.reduce_all(elements_finished)  # -> boolean scalar
            next_inputs = tf.cond(all_finished, lambda: pad_step_embedded, lambda: next_input)
            next_state = state
            return elements_finished, next_inputs, next_state

        my_helper = tf.contrib.seq2seq.CustomHelper(initial_fn, sample_fn, next_inputs_fn)

        def decode(helper, scope, reuse=None):
            with tf.variable_scope(scope, reuse=reuse):
                memory = tf.transpose(encoder_outputs, [1, 0, 2])
                attention_mechanism = tf.contrib.seq2seq.BahdanauAttention(
                    num_units=self.hidden_size, memory=memory,
                    memory_sequence_length=self.encoder_inputs_actual_length)
                cell = tf.contrib.rnn.LSTMCell(num_units=self.hidden_size * 2)
                attn_cell = tf.contrib.seq2seq.AttentionWrapper(
                    cell, attention_mechanism, attention_layer_size=self.hidden_size)
                out_cell = tf.contrib.rnn.OutputProjectionWrapper(
                    attn_cell, self.slot_size, reuse=reuse
                )
                decoder = tf.contrib.seq2seq.BasicDecoder(
                    cell=out_cell, helper=helper,
                    initial_state=out_cell.zero_state(
                        dtype=tf.float32, batch_size=self.batch_size))
                # initial_state=encoder_final_state)
                final_outputs, final_state, final_sequence_lengths = tf.contrib.seq2seq.dynamic_decode(
                    decoder=decoder, output_time_major=True,
                    impute_finished=True, maximum_iterations=self.input_steps
                )
                return final_outputs

        outputs = decode(my_helper, 'decode')
        print("outputs: ", outputs)
        print("outputs.rnn_output: ", outputs.rnn_output)
        print("outputs.sample_id: ", outputs.sample_id)
        #print('outputs.id_confidence', outputs.)
        # weights = tf.to_float(tf.not_equal(outputs[:, :-1], 0))
        self.decoder_prediction = outputs.sample_id
        decoder_max_steps, decoder_batch_size, decoder_dim = tf.unstack(tf.shape(outputs.rnn_output))
        self.decoder_targets_time_majored = tf.transpose(self.decoder_targets, [1, 0])
        self.decoder_targets_true_length = self.decoder_targets_time_majored[:decoder_max_steps]
        print("decoder_targets_true_length: ", self.decoder_targets_true_length)
        # 定义mask，使padding不计入loss计算
        self.mask = tf.to_float(tf.not_equal(self.decoder_targets_true_length, 0))
        # 定义slot标注的损失
        loss_slot = tf.contrib.seq2seq.sequence_loss(
            outputs.rnn_output, self.decoder_targets_true_length, weights=self.mask)
        # 定义intent分类的损失
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(
            labels=tf.one_hot(self.intent_targets, depth=self.intent_size, dtype=tf.float32),
            logits=intent_logits)
        loss_intent = tf.reduce_mean(cross_entropy)

        self.loss = loss_slot + loss_intent
        optimizer = tf.train.AdamOptimizer(name="a_optimizer")
        self.grads, self.vars = zip(*optimizer.compute_gradients(self.loss))
        print("vars for loss function: ", self.vars)
        gradients, _ = tf.clip_by_global_norm(self.grads, 5)  # clip gradients
        self.train_op = optimizer.apply_gradients(zip(self.grads, self.vars))
        # self.train_op = optimizer.minimize(self.loss)
        # train_op = layers.optimize_loss(
        #     loss, tf.train.get_global_step(),
        #     optimizer=optimizer,
        #     learning_rate=0.001,
        #     summaries=['loss', 'learning_rate'])

    def step(self, sess, mode, trarin_batch, word_dic):
        """ perform each batch"""
        if mode not in ['train', 'test']:
            print >> sys.stderr, 'mode is not supported'
            sys.exit(1)
        unziped = list(zip(*trarin_batch))
        #print(np.shape(unziped[0]), np.shape(unziped[1]),
        #       np.shape(unziped[2]), np.shape(unziped[3]))
        embedding = np.zeros([self.input_steps, self.batch_size, self.word_size])
        for train_data_num in range(0,self.batch_size):
            for vocab_num in range(0,self.input_steps):
                vocab = trarin_batch[train_data_num][0][vocab_num].decode("utf-8")
                for word in vocab:
                    if word in word_dic.keys():
                        index = word_dic[word]
                        embedding[vocab_num, train_data_num, index] += 1.0
                    else:
                        embedding[vocab_num, train_data_num, -1] = 1.0

        if mode == 'train':
            output_feeds = [self.train_op, self.loss, self.decoder_prediction,
                            self.intent, self.mask, self.slot_W]
            feed_dict = {
                         self.encoder_inputs_actual_length: unziped[1],
                         self.decoder_targets: unziped[2],
                         self.intent_targets: unziped[3],
                         self.embedding_npy_musk: embedding
                         }
        if mode in ['test']:
            #output_feeds = [self.decoder_prediction, self.intent]
            output_feeds = [self.decoder_prediction, self.intent, self.accuracy]
            feed_dict = {
                         self.encoder_inputs_actual_length: unziped[1],
                         self.embedding_npy_musk: embedding
                         }

        results = sess.run(output_feeds, feed_dict=feed_dict)

        return results