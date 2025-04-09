import torch.nn as nn

class DRAGON(nn.Module):
    def __init__(self, cutout_size=94, channels=1, num_classes=6):
        """
        This is the CNN model that was used for the DRAGON training.
        :param cutout_size: The size of the image, typically 94x94 representing
        8" by 8" images.

        :param channels: The number of channels of the image. For grayscale, this is 1.
        For RGB, this is 3.

        :param num_classes: Self-explanatory.
        """
        super(DRAGON, self).__init__()
        self.cutout_size = cutout_size
        self.channels = channels
        self.expected_input_shape = (
            16,
            self.channels,
            self.cutout_size,
            self.cutout_size,
        )

        self.num_classes = num_classes

        self.layer1 = nn.Sequential(
            nn.Conv2d(self.channels, 64, kernel_size=(3, 3), padding='same'),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=2)
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(64, 96, kernel_size=3, padding='same'),
            nn.BatchNorm2d(96),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=2)
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(96, 128, kernel_size=3, padding='same'),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=2)
        )
        self.layer4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding='same'),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=1),
        )

        self.layer5 = nn.Sequential(
            nn.Conv2d(256, 384, kernel_size=3, padding='same'),
            nn.BatchNorm2d(384),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=1)
        )

        self.layer6 = nn.Sequential(
            nn.Conv2d(384, 384, kernel_size=3, padding='same'),
            nn.BatchNorm2d(384),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=1)
        )
        self.layer7 = nn.Sequential(
            nn.Conv2d(384, 384, kernel_size=3, padding='same'),
            nn.BatchNorm2d(384),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=2)
        )
        self.layer8 = nn.Sequential(
            nn.Conv2d(384, 512, kernel_size=3, padding='same'),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(),
            nn.AvgPool2d(kernel_size=2, stride=2)
        )

        self.fc1 = nn.Linear(2048, 1024)
        self.drop = nn.Dropout(0.5)
        self.fc2 = nn.Linear(1024, num_classes)

    def forward(self, x):
        # Forward pass through the layers
        out = self.layer1(x)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.layer5(out)
        out = self.layer6(out)
        out = self.layer7(out)
        out = self.layer8(out)

        # Flatten the output tensor
        out = out.view(out.size(0), -1)

        # Fully connected layers
        out = self.fc1(out)
        out = self.drop(out)
        out = self.fc2(out)

        return out
