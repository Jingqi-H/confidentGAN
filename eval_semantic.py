import cv2
import os, sys
import numpy as np

import torch
import torch.utils.data
from network import FPNet
from data_loaders import LaneDataSet
from loss import bce_loss, ProbOhemCrossEntropy2d
from dice import DiceLoss
from config import config
import tools

pb = tools.pb
import torch.nn as nn
from torch.utils.data import DataLoader
from eval import compute_iou

os.environ['CUDA_VISIBLE_DEVICES'] = '2'
os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'

seed = 304
torch.manual_seed(seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed(seed)


def load_model(model, model_file, is_restore=False):
    if isinstance(model_file, str):
        state_dict = torch.load(model_file)
        if 'model' in state_dict.keys():
            state_dict = state_dict['model']
    else:
        state_dict = model_file

    #     if is_restore:
    #         new_state_dict = OrderedDict()
    #         for k, v in state_dict.items():
    #             name = 'module.' + k
    #             new_state_dict[name] = v
    #         state_dict = new_state_dict

    model.load_state_dict(state_dict, strict=False)
    ckpt_keys = set(state_dict.keys())
    own_keys = set(model.state_dict().keys())
    missing_keys = own_keys - ckpt_keys
    unexpected_keys = ckpt_keys - own_keys

    del state_dict
    return model


BATCH_SIZE = 1

val_dataset = LaneDataSet(config.eval_source)
val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=True, num_workers=config.num_workers)

base_lr = 3e-2
criterion = nn.CrossEntropyLoss(reduction='mean',
                                ignore_index=255)
ohem_criterion = ProbOhemCrossEntropy2d(ignore_label=255, thresh=0.7,
                                        min_kept=int(
                                            48 // 8 * 1024 * 1024 // 16),
                                        use_weight=False)

BatchNorm2d = nn.BatchNorm2d

model = FPNet(17, is_training=False,
              criterion=criterion,
              ohem_criterion=ohem_criterion,
              dice_criterion=None,
              pretrained_model=None,
              norm_layer=BatchNorm2d)

print(model)

print('test iou')

model_path = ''

model.load_state_dict(torch.load(model_path))
model.eval()

mean_iou = compute_iou(model.net, val_loader, config.num_workers, 1024, BATCH_SIZE, pb, 20)
print(mean_iou)
print('end')

