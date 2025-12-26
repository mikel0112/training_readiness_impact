import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from torch_dataset import get_dataloader
from xgboost import XGBRegressor

class SimpleNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class xgboost_model:
    def __init__(self):
        self.model = XGBRegressor(objective ='reg:squarederror', colsample_bytree = 0.3, learning_rate = 0.001,
                                  max_depth = 5, alpha = 10, n_estimators = 200)

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def predict(self, X):
        return self.model.predict(X)

def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs):
    train_losses = []
    val_losses = []

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        # loader contains a dictionary
        for sample in train_loader:
            inputs = sample['inputs']
            labels = sample['labels']
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)

        epoch_loss = running_loss / len(train_loader.dataset)
        train_losses.append(epoch_loss)

        model.eval()
        val_running_loss = 0.0
        with torch.no_grad():
            for sample in val_loader:
                inputs = sample['inputs']
                labels = sample['labels']
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_running_loss += loss.item() * inputs.size(0)

        val_epoch_loss = val_running_loss / len(val_loader.dataset)
        val_losses.append(val_epoch_loss)

        print(f'Epoch {epoch+1}/{num_epochs}, Train Loss: {epoch_loss:.4f}, Val Loss: {val_epoch_loss:.4f}')

    return train_losses, val_losses

def plot_losses(train_losses, val_losses):
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Training and Validation Loss')
    plt.show()

def make_predictions(model, test_loader):
    model.eval()
    predictions = []
    actuals = []
    with torch.no_grad():
        for sample in test_loader:
            inputs = sample['inputs']
            labels = sample['labels']
            outputs = model(inputs)
            predictions.extend(outputs.numpy())
            actuals.extend(labels.numpy())
    
    # plot predictions vs actuals
    plt.figure(figsize=(10, 5))
    plt.scatter(predictions, actuals)
    plt.xlabel('Predictions')
    plt.ylabel('Actuals')
    plt.xlim(0, 10)
    plt.ylim(0, 10)
    plt.title('Predictions vs Actuals')
    plt.show()

if __name__ == '__main__':

    # get data file
    data = pd.read_csv('data/unified_data_Mikel Campo.csv')

    # Split data into training, validation and test sets
    train_size = int(0.7 * len(data))
    val_size = int(0.15 * len(data))
    test_size = len(data) - train_size - val_size
    train_data, val_data, test_data = np.split(data.sample(frac=1), [train_size, train_size + val_size])

    #ask to the user which model to use
    model_typpe = input("Enter model type (nn/xgboost): ").strip().lower()

    if model_typpe == 'nn':
        # Hyperparameters
        input_size = 10
        hidden_size = 50
        output_size = 1
        num_epochs = 100
        learning_rate = 0.001
        batch_size = 4
        
        # Get data loaders
        train_loader = get_dataloader(df=train_data, batch_size=batch_size, shuffle=True)
        val_loader = get_dataloader(df=val_data, batch_size=batch_size, shuffle=False)

        # Initialize model, criterion, and optimizer
        model = SimpleNN(input_size, hidden_size, output_size)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        # Train the model
        train_losses, val_losses = train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs)

        # Plot the losses
        plot_losses(train_losses, val_losses)

        # Make predictions on the test set
        test_loader = get_dataloader(df=test_data, batch_size=batch_size, shuffle=False)
        make_predictions(model, test_loader)
    elif model_typpe == 'xgboost':
        # split data into training, validation and test sets
        train_size = int(0.7 * len(data))
        val_size = int(0.15 * len(data))
        test_size = len(data) - train_size - val_size
        train_data, val_data, test_data = np.split(data.sample(frac=1), [train_size, train_size + val_size])
        # prepare data for xgboost
        X_train = train_data.drop(columns=['date', 'session_quality','icu_rpe','feel','icu_efficiency_factor','end_power','end_heartrate'])
        y_train = train_data['session_quality']
        X_val = val_data.drop(columns=['date', 'session_quality','icu_rpe','feel','icu_efficiency_factor','end_power','end_heartrate'])
        y_val = val_data['session_quality']
        X_test = test_data.drop(columns=['date', 'session_quality','icu_rpe','feel','icu_efficiency_factor','end_power','end_heartrate'])
        y_test = test_data['session_quality']
        # train model
        model = xgboost_model()
        model.train(X_train, y_train)
        # show training curves
        y_val_pred = model.predict(X_val)
        val_mse = np.mean((y_val - y_val_pred) ** 2)
        print(f"Validation MSE: {val_mse}")
        # make predictions on the test set
        y_pred = model.predict(X_test)
        # plot predictions vs actuals
        plt.figure(figsize=(10, 5))
        plt.scatter(y_pred, y_test)
        plt.xlabel('Predictions')
        plt.ylabel('Actuals')
        plt.title('Predictions vs Actuals')
        plt.show()

