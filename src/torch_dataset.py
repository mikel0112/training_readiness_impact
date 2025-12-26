from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import torch
import pandas as pd
import numpy as np
import os
import datetime

class CustomTorchDataset(Dataset):
    def __init__(self, df, transform=None):
        """
        Args:
            df (string): Path to the csv file with annotations.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.data = df
        self.transform = transform

        # data normalization using pandas automatically every column except date and label
        cols_to_normalize = self.data.columns.difference(['date', 'session_quality'])
        self.data[cols_to_normalize] = (self.data[cols_to_normalize] - self.data[cols_to_normalize].mean()) / self.data[cols_to_normalize].std()
        # fill na
        self.data = self.data.fillna(0).reset_index(drop=True)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        wellness_sample = self.data.iloc[idx].to_dict()
        
        sample = {
            'date': wellness_sample['date'],
            # convert date to float
            'date_float': torch.tensor(datetime.datetime.strptime(wellness_sample['date'], '%Y-%m-%d').timestamp(), dtype=torch.float32),
            'ramp_rate': torch.tensor(wellness_sample['rampRate'], dtype=torch.float32),
            'weight': torch.tensor(wellness_sample['weight'], dtype=torch.float32),
            'restinghr': torch.tensor(wellness_sample['restingHR'], dtype=torch.float32),
            'hrv': torch.tensor(wellness_sample['hrv'], dtype=torch.float32),
            'sleepsecs': torch.tensor(wellness_sample['sleepSecs'], dtype=torch.float32),
            'stress': torch.tensor(wellness_sample['stress'], dtype=torch.float32),
            'motivation': torch.tensor(wellness_sample['motivation'], dtype=torch.float32),
            'injury': torch.tensor(wellness_sample['injury'], dtype=torch.float32),
            'start_power': torch.tensor(wellness_sample['start_power'], dtype=torch.float32),
            'start_hr': torch.tensor(wellness_sample['start_heartrate'], dtype=torch.float32),
            'label': torch.tensor(wellness_sample['session_quality'], dtype=torch.float32)
        }

        sample = {
            'inputs': torch.tensor([
                sample['ramp_rate'],
                sample['weight'],
                sample['restinghr'],
                sample['hrv'],
                sample['sleepsecs'],
                sample['stress'],
                sample['motivation'],
                sample['injury'],
                sample['start_power'],
                sample['start_hr']
            ], dtype=torch.float32),
            'labels': torch.tensor(sample['label'], dtype=torch.float32)
        }

        return sample

def get_dataloader(df, batch_size=16, shuffle=True, transform=None):
    dataset = CustomTorchDataset(df=df, transform=transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    return dataloader

