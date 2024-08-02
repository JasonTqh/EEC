import tensorflow as tf
from model import AlexNet

# loading dataset
def preprocess_image(image, label):
    image = tf.image.resize(image, [227, 227])  # Resize to the input size of AlexNet
    image = tf.cast(image, tf.float32)
    image /= 255.0  # Normalize to [0, 1]
    return image, label

def make_dataset():
    # Load the CIFAR-10 dataset
    (train_images, train_labels), _ = tf.keras.datasets.cifar10.load_data()
    train_dataset = tf.data.Dataset.from_tensor_slices((train_images, train_labels))
    train_dataset = train_dataset.map(preprocess_image).batch(128).shuffle(1000)
    return train_dataset


def train_model_stop(model, dataset, stop_layer):
    for x, y in dataset:
        with tf.GradientTape() as tape:
            predictions = model(x, training=True)
            loss = tf.keras.losses.sparse_categorical_crossentropy(y, predictions)

        # Get weights that need to be updated (train only to the specified layer)
        trainable_vars = model.trainable_variables[:stop_layer]
        gradients = tape.gradient(loss, trainable_vars)
        model.optimizer.apply_gradients(zip(gradients, trainable_vars))

def train_and_evaluate(model, dataset, epochs=1):
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.fit(dataset, epochs=epochs)




if __name__ == '__main__':

    max_layers = 14  # AlexNet has 14 layers in total
    dataset = make_dataset()  # Load dataset

    for d in range(max_layers + 1):
        for e in range(max_layers + 1):
            if d <= e:  # To avoid duplicate models and ensure m <= e
                model_d = AlexNet(d)
                model_e = AlexNet(e)
                model_full = AlexNet(max_layers)  # Full model

                print(f"Training model up to layer {d}")
                # train_and_evaluate(model_d, dataset)

                # transfer_and_aggregate_parameters(model_d, model_e)

                print(f"Training model up to layer {e}")

                # train_and_evaluate(model_e, dataset)

                print("Training full model")
                # train_and_evaluate(model_full, dataset)
