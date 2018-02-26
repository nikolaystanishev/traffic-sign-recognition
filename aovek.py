import argparse
import json

from aovek.preprocess.download_dataset import download_dataset
from aovek.preprocess.data_processing import DataProcessing
from aovek.training.train import Train
from aovek.visualization.predict import Predict
from aovek.validate.eval_metrics import EvalMetrics

parser = argparse.ArgumentParser(description='''
4ovek:
    File for contolling people detection process
''')
parser._action_groups.pop()

required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')

required.add_argument('-config_file', help='Path to config file.',
                      required=True)

optional.add_argument('-dataset_download', help='Download dataset.',
                      action='store_true')
optional.add_argument('-processes_dataset', help='Processes dataset.',
                      action='store_true')
optional.add_argument('-train', help='Train convolutional neural network.',
                      action='store_true')
optional.add_argument('-predict', help='Make predictions for entire dataset.',
                      action='store_true')
optional.add_argument('-evaluate', help='Evaluate trained model.',
                      action='store_true')


def dataset_download(config):
    download_dataset(config)


def processes_dataset(config):
    dp = DataProcessing(config)
    dp.pickle_dataset()

    print('Taken time: {}'.format(str(dp.get_time())))


def train(config):
    train = Train(config)
    train.load_dataset()
    train.train(config)


def predict(config):
    predict = Predict(config)
    predict.make_predictions_for_datasets()


def evaluate(config):
    eval_metrics = EvalMetrics(config)
    eval_metrics.eval_pickles_metrics()


if __name__ == '__main__':
    args = parser.parse_args()

    config_file = args.config_file

    with open(config_file) as c_f:
        config = json.load(c_f)

    if args.dataset_download:
        dataset_download(config)
    elif args.processes_dataset:
        processes_dataset(config)
    elif args.train:
        train(config)
    elif args.predict:
        predict(config)
    elif args.evaluate:
        evaluate(config)