import pickle
import numpy as np
import tensorflow as tf
import pynvml
import psutil
import socket
import time as tm
from model import AlexNet
import os

# loading dataset
def unpickle(file):
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict
def load_cifar10_data(data_dir):
    train_data = None
    train_labels = []

    for i in range(1, 6):
        data_path = os.path.join(data_dir, f"data_batch_{i}")
        batch_data = unpickle(data_path)
        if train_data is None:
            train_data = batch_data[b'data']
        else:
            train_data = np.vstack((train_data, batch_data[b'data']))
        train_labels += batch_data[b'labels']

    train_data = train_data.reshape((len(train_data), 3, 32, 32))
    train_data = np.transpose(train_data, (0, 2, 3, 1))

    return train_data, np.array(train_labels)
def preprocess_image(image, label):
    image = tf.image.resize(image, [227, 227])  # Resize to the input size of AlexNet
    image = tf.cast(image, tf.float32)
    image /= 255.0  # Normalize to [0, 1]
    label = tf.one_hot(label, depth=10)
    return image, label
# def make_dataset(single_sample=False):
#     # Load the CIFAR-10 dataset
#     (train_images, train_labels), _ = tf.keras.datasets.cifar10.load_data()
#     train_dataset = tf.data.Dataset.from_tensor_slices((train_images, train_labels))
#     train_dataset = train_dataset.map(preprocess_image)
#     if not single_sample:
#         train_dataset = train_dataset.batch(128).shuffle(1000)
#     return train_dataset
# /app/data/cifar-10-batches-py/
def make_dataset(single_sample=False, data_dir="cifar-10-batches-py/"):
    train_images, train_labels = load_cifar10_data(data_dir)
    train_dataset = tf.data.Dataset.from_tensor_slices((train_images, train_labels))
    train_dataset = train_dataset.map(preprocess_image)
    if not single_sample:
        train_dataset = train_dataset.batch(128).shuffle(1000)
    return train_dataset




def get_time(alexNet, data_set):
    iterator = iter(data_set)
    image, label = next(iterator)
    label = tf.expand_dims(label, axis=0)  # 添加批次维度
    # Add Batch Dimension，because the model expects four-dimensional inputs (batch_size, height, width, channels)
    image = tf.expand_dims(image, axis=0)
    training_times = {
        "forward": [],
        "backward": [],
        "update": []
    }
    with tf.GradientTape(persistent=True) as tape:
        x = image
        intermediates = []
        for layer in alexNet.model.layers:
            start_time = tm.time()
            x = layer(x)
            intermediates.append(x)
            training_times['forward'].append(tm.time() - start_time)
        loss = tf.reduce_mean(tf.losses.categorical_crossentropy(label, x, from_logits=False))

    for idx, layer in enumerate(alexNet.model.layers):
        if layer.trainable_variables:  # Only compute for layers with parameters
            start_time = tm.time()
            grads = tape.gradient(loss, layer.trainable_variables)
            training_times["backward"].append(tm.time() - start_time)
            # 更新参数
            start_time = tm.time()
            tf.keras.optimizers.Adam().apply_gradients(zip(grads, layer.trainable_variables))
            training_times["update"].append(tm.time() - start_time)
        else:
            training_times["backward"].append(0)
            training_times["update"].append(0)

    return training_times
# Get the performance of the current device
def get_device_performance():
    # Get the number of gpu of the current device
    # pynvml.nvmlInit()
    # gpu_count = pynvml.nvmlDeviceGetCount()
    # print("GPU count:", gpu_count)
    # pynvml.nvmlShutdown()

    # Get the number of cpu of the current device
    # cpu_count = psutil.cpu_count(logical=True)
    cpu_count = 8
    print("logical CPUs count:", cpu_count)
    # Get the RAM size of the current device
    # ram_info = psutil.virtual_memory()
    # ram = ram_info.total / (1024 ** 3)
    ram = 4
    print("RAM: ", ram, "GB")


def send_edge_server_info(data, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        data = pickle.dumps((data))
        print(data)
        s.sendall(data)
        s.close()
def receive_cloud_info(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        s.settimeout(180)

        try:
            conn, addr = s.accept()
            with conn:
                conn.settimeout(60)
                data = b''
                while True:
                    try:
                        packet = conn.recv(4096)
                        if not packet:
                            break
                        data += packet
                    except socket.timeout:
                        print("Connection timed out while receiving data")
                        break
                if data:
                    params = pickle.loads(data)
                    return params
        except socket.timeout:
            print("No connection was made within the timeout period.")
        except Exception as e:
            print(f"An error occurred: {e}")
    return None
def receive_device_info(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        s.settimeout(180)
        try:
            conn, addr = s.accept()
            with conn:
                conn.settimeout(60)
                data = b''
                while True:
                    try:
                        packet = conn.recv(4096)
                        if not packet:
                            break
                        data += packet
                    except socket.timeout:
                        print("Connection timed out while receiving data")
                        break
                if data:
                    params = pickle.loads(data)
                    return params
        except socket.timeout:
            print("No connection was made within the timeout period.")
        except Exception as e:
            print(f"An error occurred: {e}")
    return None
def receive_number_sample(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        s.settimeout(180)
        try:
            conn, addr = s.accept()
            with conn:
                conn.settimeout(60)
                data = b''
                while True:
                    try:
                        packet = conn.recv(4096)
                        if not packet:
                            break
                        data += packet
                    except socket.timeout:
                        print("Connection timed out while receiving data")
                        break
                if data:
                    params = pickle.loads(data)
                    return params
        except socket.timeout:
            print("No connection was made within the timeout period.")
        except Exception as e:
            print(f"An error occurred: {e}")
    return None
def send_edge_device_parameters(parameters, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(parameters)

# training process
# data-parallel
def train_model_stop(model, data_set, stop_layer):
    for x, y in data_set:
        with tf.GradientTape() as tape:
            predictions = model(x, training=True)
            loss = tf.keras.losses.sparse_categorical_crossentropy(y, predictions)

        # Get weights that need to be updated (train only to the specified layer)
        trainable_vars = model.trainable_variables[:stop_layer]
        gradients = tape.gradient(loss, trainable_vars)
        model.optimizer.apply_gradients(zip(gradients, trainable_vars))
def train_and_evaluate(model, data_set, epochs=1):
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.fit(data_set, epochs=epochs)

if __name__ == "__main__":
    # host = ['172.18.0.10', '172.18.0.11', '172.18.0.12']
    # port = [9090, 9091, 9092]
    max_layers = 14
    # cloud_info = receive_cloud_info('172.18.0.2', 8080 )
    # layers = cloud_info
    model = AlexNet(max_layers)
    print("Model loaded.")
    single_sample_data_set = make_dataset(single_sample=True)
    data_set = make_dataset()
    print("Dataset loaded.")
    train_times = get_time(model, single_sample_data_set)
    print(train_times)
    # score = get_device_performance()
    send_edge_server_info(train_times, '172.18.0.2', 8080)
    # number_sample_start, number_sample_end = receive_number_sample('172.18.0.2', 8080)
    # md = receive_cloud_info('172.18.0.2', 8080)
    # data_set_edge = data_set.skip(number_sample_start).take(number_sample_start, number_sample_end)
    # train_model_stop(model, data_set_edge, md)
    # weights = model.get_weights()
    # weights_d=[]
    # weights_d[0] = receive_device_info(host[0], port[0])
    # weights_d[1] = receive_device_info(host[1], port[1])
    # weights_d[2] = receive_device_info(host[2], port[2])
    # for i in range(md):
    #     weights[i] = (weights_d[0][i] + weights_d[1][i]+weights_d[2][i]) / 3  # 简单平均聚合
    # model.set_weights(weights)
    # train_model_stop(model, data_set_edge, layers)
    # weights = model.get_weights()
    # send_edge_device_parameters(weights, '172.18.0.2', 8080)
