# This layer is very simple, the function is stop the BP stream pass
# to the lower layer.

import caffe


class StopBPLayer(caffe.Layer):
    """
    This layer cut the BP stream, which indicate it will not pass
    the diff to the lower layer.
    So, it takes NO parameters
    """
    def setup(self, bottom, top):
        # Reshap the top
        self.blobs_num = len(bottom)
        self.reshape(bottom, top)

    def reshape(self, bottom, top):
        for i in range(self.blobs_num):
            top[i].reshape(*bottom[i].shape)

    def forward(self, bottom, top):
        for i in range(self.blobs_num):
            top[i].data[...] = bottom[i].data

    def backward(self, top, propagate_down, bottom):
        # Set diff to zero, cut all BP
        for i in range(self.blobs_num):
            bottom[i].diff[...] = 0
