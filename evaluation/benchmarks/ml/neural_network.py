import torch

from time import time


import data_loader
import network_generator
import accuracy

# Characteristics inherent to the dataset
INPUT_SIZE = 28**2 # Images are 28px * 28px
OUTPUT_SIZE  = 10

# Neural network characteristics
HIDDEN_LAYER_SIZES = [128, 64]
BATCH_SIZE = 32
EPOCHS = 15

USE_GPU = True

def set_device() -> torch.device:
    """ Sets the device to train the model on between GPU and CPU

    Returns:
        torch.device: The appropriate device
    """
    if torch.cuda.is_available() and USE_GPU:
        print('Using Cuda')
        return torch.device('cuda:0')
    else:
        print('Using CPU')
        return torch.device('cpu')

def train_batch(batch: torch.Tensor, labels: torch.Tensor, print_time) -> float:
    """ Trains the model for a batch of training data.

    Args:
        batch (torch.Tensor): the batch to train on
        labels (torch.Tensor): the label of the data

    Returns:
        float: the loss value from training this batch
    
    Currently relies on global variables for convenience. Should consider taking
    them as arguments if this were to be a separate script
    """
    batch_start_time = time()

    # flattens size 28*28 matrix to length 784 array
    batch = batch.view(batch.shape[0], -1)
    flatten_batch_time = time()

    # zero out gradients left over from previous iteration
    optimizer.zero_grad()
    zero_grad_time = time()

    # potential for pipelining
    output = model(batch)
    output_time = time()
    loss = criterion(output, labels)
    loss_time = time()

    # back propagation
    loss.backward()
    back_prop_time = time()

    # weight optimization
    optimizer.step()
    optimizer_time = time()

    if print_time:
        print(f'flatten_batch_time: {flatten_batch_time - batch_start_time}')
        print(f'zero_grad_time: {zero_grad_time - flatten_batch_time}')
        print(f'output_time: {output_time - zero_grad_time}')
        print(f'loss_time: {loss_time - output_time}')
        print(f'back_prop_time: {back_prop_time - loss_time}')
        print(f'optimizer_time: {optimizer_time - back_prop_time}')

    return loss.item()

def train_epoch(n: int, train_loader: torch.Tensor):
    running_loss = 0
    # iterates over each batch in the train dataset
    for images, labels in train_loader:
        running_loss += train_batch(batch=images.to(device=device), 
                                    labels=labels.to(device=device),
                                    print_time=False)
    print(f'Epoch {n} Loss: {running_loss / len(train_loader)}')

def main():
    global model, criterion, optimizer, device
    device = set_device()
    model, criterion, optimizer = network_generator.prepare_environment()
    train_loader, test_loader = data_loader.load_data(BATCH_SIZE)

    time_0 = time()
    print('Begin Training...')

    for n in range(EPOCHS):
        train_epoch(n, train_loader)

    print(f'Training time: {time() - time_0}')

    accuracy.calc_accuracy(model, test_loader, device)

if (__name__ == '__main__'):
    main()