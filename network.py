from keras.models import Model
from keras.layers import Input, Conv2D, MaxPooling2D, Reshape
from keras.models import load_model
from keras.models import model_from_json
from keras.callbacks import History
from keras.optimizers import SGD, Adam, RMSprop, Adagrad, Adadelta, Adamax,\
    Nadam
from keras.initializers import RandomNormal
import json
import numpy as np

from metrics import precision, recall, fmeasure

import tensorflow as tf
sess = tf.Session(config=tf.ConfigProto(log_device_placement=True))


class YOLO:
    """
        Class for YOLO Convolutional neural network
    """

    def __init__(self, config):
        self.image_size = config['image_info']['image_size']
        self.color_channels = config['image_info']['color_channels']

        self.grid_size = config['label_info']['grid_size']
        self.number_of_classes = config['label_info']['number_of_classes']
        self.number_of_annotations =\
            config['label_info']['number_of_annotations']

        self.batch_size = config['network']['train']['batch_size']
        self.number_of_epochs = config['network']['train']['number_of_epochs']

        self.alpha_coord = config['network']['train']['loss']['alpha_coord']
        self.alpha_noobj = config['network']['train']['loss']['alpha_noobj']

        self.learning_rate =\
            config['network']['train']['optimizer']['learning_rate']
        self.momentum = config['network']['train']['optimizer']['momentum']
        self.decay = config['network']['train']['optimizer']['decay']

        self.optimizer = None

        self.history = History()

        self.metrics = None
        self.model_structure = None

        self.model_binary_data_file =\
            config['network']['model_binary_data_file']
        self.model_json_structure_file =\
            config['network']['json_model_structure']

        self.model = self.create_model()

    def create_model(self):
        input = Input(shape=(self.image_size, self.image_size,
                             self.color_channels))

        network = self.create_network(input)

        model = Model(input, network)

        self.optimizer = self.create_optimizer()

        model.compile(optimizer=self.optimizer,
                      loss=self.custom_loss,
                      metrics=['accuracy', precision, recall, fmeasure])

        model.summary()
        return model

    def create_network(self, input):
        network = Conv2D(filters=32,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_1',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(input)
        network = MaxPooling2D(pool_size=(2, 2),
                               name='pool_1')(network)

        network = Conv2D(filters=64,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_2',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = MaxPooling2D(pool_size=(2, 2),
                               name='pool_2')(network)

        network = Conv2D(filters=128,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_3',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=64,
                         kernel_size=(1, 1),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_4',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=128,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_5',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = MaxPooling2D(pool_size=(2, 2),
                               name='pool_3')(network)

        network = Conv2D(filters=256,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_6',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=128,
                         kernel_size=(1, 1),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_7',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=256,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_8',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = MaxPooling2D(pool_size=(2, 2),
                               name='pool_4')(network)

        network = Conv2D(filters=512,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_9',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=256,
                         kernel_size=(1, 1),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_10',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=512,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_11',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=256,
                         kernel_size=(1, 1),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_12',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = Conv2D(filters=512,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_13',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)
        network = MaxPooling2D(pool_size=(2, 2),
                               name='pool_5')(network)

        network = Conv2D(filters=1024,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_14',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)

        network = Conv2D(filters=1024,
                         kernel_size=(3, 3),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_15',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)

        network = Conv2D(filters=(self.number_of_annotations + 1 +
                                  self.number_of_classes),
                         kernel_size=(1, 1),
                         strides=(1, 1),
                         padding='same',
                         activation='relu',
                         name='conv_16',
                         kernel_initializer=RandomNormal(),
                         use_bias=False)(network)

        network = Reshape((self.grid_size,
                           self.grid_size,
                           (self.number_of_annotations + 1 +
                            self.number_of_classes)))(network)

        return network

    def create_optimizer(self):
        # optimizer = SGD()
        # optimizer = RMSprop()
        # optimizer = Adagrad()
        # optimizer = Adadelta()
        # optimizer = Adam()
        # optimizer = Adamax()
        # optimizer = Nadam()

        optimizer = SGD(lr=self.learning_rate,
                        momentum=self.momentum,
                        decay=self.decay)
        # optimizer = Adam(lr=self.learning_rate,
        #                  decay=self.decay)

        return optimizer

    def train(self, train_data, train_labels, validation_data,
              validation_labels):
        self.model.fit(train_data, train_labels,
                       batch_size=self.batch_size,
                       epochs=self.number_of_epochs,
                       validation_data=(validation_data, validation_labels),
                       shuffle=True,
                       callbacks=[self.history])

    def custom_loss(self, true, pred):
        loss = 0

        true =\
            tf.reshape(true, shape=(-1, self.grid_size ** 2,
                                    (self.number_of_annotations + 1 +
                                     self.number_of_classes)))
        pred =\
            tf.reshape(pred, shape=(-1, self.grid_size ** 2,
                                    (self.number_of_annotations + 1 +
                                     self.number_of_classes)))

        x_true = true[:, :, 0]
        x_pred = pred[:, :, 0]

        y_true = true[:, :, 1]
        y_pred = pred[:, :, 1]

        w_true = true[:, :, 2]
        w_pred = pred[:, :, 2]

        h_true = true[:, :, 3]
        h_pred = pred[:, :, 3]

        if self.number_of_classes >= 0:
            c_true = true[:, :, 4]
            c_pred = pred[:, :, 4]

        if self.number_of_classes >= 1:
            p_true = true[:, :, 5]
            p_pred = pred[:, :, 5]

        loss +=\
            np.sum(
                tf.scalar_mul(
                    self.alpha_coord,
                    tf.multiply(
                        p_true,
                        tf.add(tf.squared_difference(x_true, x_pred),
                               tf.squared_difference(y_true, y_pred)))))

        loss +=\
            np.sum(
                tf.scalar_mul(
                    self.alpha_coord,
                    tf.multiply(
                        p_true,
                        tf.add(tf.squared_difference(tf.sqrt(w_true),
                                                     tf.sqrt(w_pred)),
                               tf.squared_difference(tf.sqrt(h_true),
                                                     tf.sqrt(h_pred))))))

        if self.number_of_classes >= 0:
            loss += np.sum(tf.multiply(p_true,
                                       tf.squared_difference(c_true, c_pred)))

            loss += np.sum(tf.scalar_mul(self.alpha_noobj,
                                         tf.multiply(
                                             p_true,
                                             tf.squared_difference(c_true,
                                                                   c_pred))))

        if self.number_of_classes >= 1:
            loss += np.sum(tf.multiply(p_true,
                                       tf.squared_difference(p_true, p_pred)))

        return loss

    def predict(self, image):
        predict = self.model.predict(image)

        return predict

    def save_model(self):
        self.model.save(self.model_binary_data_file)

    def load_model(self):
        custom_objects = self.get_custom_objects()
        self.model = load_model(self.model_binary_data_file,
                                custom_objects=custom_objects)

    def load_model_file(self, model_file):
        custom_objects = self.get_custom_objects()
        self.model = load_model(model_file,
                                custom_objects=custom_objects)

    def save_json_model_structure(self):
        json_model_structure = self.model.to_json()

        with open(self.model_json_structure_file, 'w') as f:
            json.dump(json_model_structure, f)

    def load_model_from_json_structure(self):
        custom_objects = self.get_custom_objects()
        self.model = model_from_json(self.model_json_structure_file,
                                     custom_objects=custom_objects)

    def get_custom_objects(self):
        custom_objects = {"precision": precision, "recall": recall,
                          "fmeasure": fmeasure,
                          "custom_loss": self.custom_loss}

        return custom_objects

    def summary(self, train_data, train_labels, validation_data,
                validation_labels, test_data, test_labels):
        self.metrics =\
            self.genarate_metrics(train_data, train_labels, validation_data,
                                  validation_labels, test_data, test_labels)
        self.model_structure = self.genarate_model_structure()

    def genarate_metrics(self, train_data, train_labels, validation_data,
                         validation_labels, test_data, test_labels):
        metrics =\
            self.get_metrics_values(train_data, train_labels, validation_data,
                                    validation_labels, test_data, test_labels)

        return metrics

    def genarate_model_structure(self):
        model_structure = []
        self.model.summary(print_fn=lambda row: model_structure.append(row))
        model_structure = '\n'.join(model_structure)

        return model_structure

    def get_metrics_values(self, train_data, train_labels, validation_data,
                           validation_labels, test_data, test_labels):
        test_metrics = self.model.evaluate(test_data, test_labels)
        train_metrics = self.model.evaluate(train_data, train_labels)
        validation_metrics =\
            self.model.evaluate(validation_data, validation_labels)

        loss = {'test_loss': test_metrics[0],
                'train_loss': train_metrics[0],
                'validation_loss': validation_metrics[0]}

        accuracy = {'test_accuracy': test_metrics[1],
                    'train_accuracy': train_metrics[1],
                    'validation_accuracy': validation_metrics[1]}

        precision = {'test_precision': test_metrics[2],
                     'train_precision': train_metrics[2],
                     'validation_precision': validation_metrics[2]}

        recall = {'test_recall': test_metrics[3],
                  'train_recall': train_metrics[3],
                  'validation_recall': validation_metrics[3]}

        f1_score = {'test_f1_score': test_metrics[4],
                    'train_f1_score': train_metrics[4],
                    'validation_f1_score': validation_metrics[4]}

        return {'loss': loss, 'accuracy': accuracy, 'precision': precision,
                'recall': recall, 'f1_score': f1_score}

    def get_metrics(self):
        return self.metrics

    def get_model_structure(self):
        return self.model_structure

    def get_model_history(self):
        return self.history.history

    def get_optimizer_params(self):
        return self.optimizer.get_config()

    def get_optimizer_type(self):
        return type(self.optimizer)

    def get_batch_size(self):
        return self.batch_size
