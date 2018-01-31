import numpy as np
import pickle
import json
import tensorflow as tf
import keras.backend as K

from network import YOLO


def precision(y_true, y_pred):
    '''Calculates the precision, a metric for multi-label classification of
    how many selected items are relevant.
    '''
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision


def recall(y_true, y_pred):
    '''Calculates the recall, a metric for multi-label classification of
    how many relevant items are selected.
    '''
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall


def fbeta_score(y_true, y_pred, beta=1):
    '''Calculates the F score, the weighted harmonic mean of precision and recall.

    This is useful for multi-label classification, where input samples can be
    classified as sets of labels. By only using accuracy (precision) a model
    would achieve a perfect score by simply assigning every class to every
    input. In order to avoid this, a metric should penalize incorrect class
    assignments as well (recall). The F-beta score (ranged from 0.0 to 1.0)
    computes this, as a weighted mean of the proportion of correct class
    assignments vs. the proportion of incorrect class assignments.

    With beta = 1, this is equivalent to a F-measure. With beta < 1, assigning
    correct classes becomes more important, and with beta > 1 the metric is
    instead weighted towards penalizing incorrect class assignments.
    '''
    if beta < 0:
        raise ValueError('The lowest choosable beta is zero (only precision).')

    # If there are no true positives, fix the F score at 0 like sklearn.
    if K.sum(K.round(K.clip(y_true, 0, 1))) == 0:
        return 0

    p = precision(y_true, y_pred)
    r = recall(y_true, y_pred)
    bb = beta ** 2
    fbeta_score = (1 + bb) * (p * r) / (bb * p + r + K.epsilon())
    return fbeta_score


def fmeasure(y_true, y_pred):
    '''Calculates the f-measure, the harmonic mean of precision and recall.
    '''
    return fbeta_score(y_true, y_pred, beta=1)


class EvalMetrics:

    def __init__(self, config):
        self.iou_threshold = config['network']['predict']['iou_threshold']
        self.prob_threshold = config['network']['predict']['prob_threshold']

        self.image_size = config['image_info']['image_size']
        self.number_of_annotations =\
            config['label_info']['number_of_annotations']

        self.network = YOLO(config)
        self.network.load_model()

        self.train_pickle_name = config['dataset']['pickle_name']['train']
        self.validation_pickle_name =\
            config['dataset']['pickle_name']['validation']
        self.test_pickle_name = config['dataset']['pickle_name']['test']

    def eval_pickles_metrics(self):
        train_data, train_labels, validation_data, validation_labels,\
            test_data, test_labels = self.load_data()

        print('Train:')
        self.eval_dataset_metrics(train_data, train_labels)

        print('Validation:')
        self.eval_dataset_metrics(validation_data, validation_labels)

        print('Test:')
        self.eval_dataset_metrics(test_data, test_labels)

    def eval_dataset_metrics(self, data, labels):
        avg_iou, accuracy, precision, recall, f1_score =\
            self.eval_metrics(data, labels)

        print('IOU: {}, Accuracy: {}, Precision: {}, Recall: {}, F1 Score: {}'
              .format(avg_iou, accuracy, precision, recall, f1_score))

    def load_data(self):
        train_data, train_labels =\
            self.get_data_from_pickle(self.train_pickle_name)
        validation_data, validation_labels =\
            self.get_data_from_pickle(self.validation_pickle_name)
        test_data, test_labels =\
            self.get_data_from_pickle(self.test_pickle_name)

        return train_data, train_labels, validation_data, validation_labels,\
            test_data, test_labels

    def get_data_from_pickle(self, pickle_name):
        with open(pickle_name, 'rb') as dsp:
            dataset = pickle.load(dsp)
            data = dataset['data']
            labels = dataset['labels']
            del dataset
        return data, labels

    def eval_metrics(self, data, labels):
        labels =\
            np.reshape(labels, (-1, self.grid_size ** 2,
                                (self.number_of_annotations + 1)))

        iou, gt_num, tp, fp, fn = self.get_metrics_params(data, labels)

        iou, accuracy, precision, recall, f1_score =\
            self.calculate_metrics(iou, gt_num, tp, fp, fn)

        return iou, accuracy, precision, recall, f1_score

    def get_metrics_params(self, images, labels):
        iou = 0
        gt_num = 0

        tp = 0
        fp = 0
        fn = 0

        for image, label in zip(images, labels):
            iou_image, gt_num_image, tp_image, fp_image, fn_image =\
                self.get_one_image_metrics_params(image, label)

            iou += iou_image
            gt_num += gt_num_image

            tp += tp_image
            fp += fp_image
            fn += fn_image

        return iou, gt_num, tp, fp, fn

    def get_one_image_metrics_params(self, image, label):
        gt = label[np.where(label[:, 4] == 1)]
        gt = self.get_corners_from_labels(gt)

        image = np.expand_dims(image, axis=0)
        pred = self.network.predict_boxes(image)
        pred[:, :4] = pred[:, :4] * self.image_size

        iou_image = self.get_iou_for_image(gt, pred)

        iou, gt_num, tp, fp, fn =\
            self.get_metrics_params_from_iou(iou_image, gt, pred)

        return iou, gt_num, tp, fp, fn

    def get_iou_for_image(self, gt, pred):
        iou_image = np.ndarray(shape=(0, pred.shape[0]),
                               dtype=np.float32)

        for box in gt:
            gt_box = np.full(pred.shape, box)

            iou_box = self.boxes_iou(gt_box, pred)

            iou_box = np.expand_dims(iou_box, axis=0)
            iou_image = np.concatenate((iou_image, iou_box))

        return iou_image

    def get_metrics_params_from_iou(self, iou_image, gt, pred):
        if iou_image.shape[1] != 0:
            iou_image = np.amax(iou_image, axis=1)
            iou_image = iou_image.flatten()

            gt_num = gt.shape[0]

            true_boxes =\
                iou_image[np.where(iou_image >= self.iou_threshold)]

            tp = true_boxes.shape[0]
            fp = pred.shape[0] - true_boxes.shape[0]
            fn = gt.shape[0] - true_boxes.shape[0]
            iou = np.sum(true_boxes)
        else:
            iou = 0
            gt_num = gt.shape[0]

            tp = 0
            fp = pred.shape[0]
            fn = gt.shape[0]

        return iou, gt_num, tp, fp, fn

    def calculate_metrics(self, iou, gt_num, tp, fp, fn):
        iou = iou / tp

        accuracy = tp / gt_num

        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        f1_score = (2 * precision * recall) / (precision + recall)

        return iou, accuracy, precision, recall, f1_score

    def get_corners_from_labels(self, labels):
        corners = np.array(labels, copy=True)

        corners[:, 0] =\
            (labels[:, 0] - (labels[:, 2] / 2)) * self.image_size
        corners[:, 1] =\
            (labels[:, 1] - (labels[:, 3] / 2)) * self.image_size
        corners[:, 2] =\
            (labels[:, 0] + (labels[:, 2] / 2)) * self.image_size
        corners[:, 3] =\
            (labels[:, 1] + (labels[:, 3] / 2)) * self.image_size

        return corners

    def boxes_iou(self, box1, box2):
        ymin_1 = np.minimum(box1[:, 0], box1[:, 2])
        xmin_1 = np.minimum(box1[:, 1], box1[:, 3])
        ymax_1 = np.maximum(box1[:, 0], box1[:, 2])
        xmax_1 = np.maximum(box1[:, 1], box1[:, 3])
        ymin_2 = np.minimum(box2[:, 0], box2[:, 2])
        xmin_2 = np.minimum(box2[:, 1], box2[:, 3])
        ymax_2 = np.maximum(box2[:, 0], box2[:, 2])
        xmax_2 = np.maximum(box2[:, 1], box2[:, 3])

        area_1 = (ymax_1 - ymin_1) * (xmax_1 - xmin_1)
        area_2 = (ymax_2 - ymin_2) * (xmax_2 - xmin_2)

        ymin_inter = np.maximum(ymin_1, ymin_2)
        xmin_inter = np.maximum(xmin_1, xmin_2)
        ymax_inter = np.minimum(ymax_1, ymax_2)
        xmax_inter = np.minimum(xmax_1, xmax_2)

        area_inter = (np.maximum(ymax_inter - ymin_inter, 0.0) *
                      np.maximum(xmax_inter - xmin_inter, 0.0))

        iou = area_inter / (area_1 + area_2 - area_inter)

        iou[np.where(area_1 < 0) or np.where(area_2 < 0)] = 0

        return iou


if __name__ == '__main__':
    with open('./config.json') as config_file:
        config = json.load(config_file)

    with tf.Session():
        eval_metrics = EvalMetrics(config)
        eval_metrics.eval_pickles_metrics()
