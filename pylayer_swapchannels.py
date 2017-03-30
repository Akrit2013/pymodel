# This pylayer can swap the channel of the blob to a certain order
# It can be used with group mechenism since the group method only
# group the near by channels


import caffe
import yaml


class SwapChannelsLayer(caffe.Layer):
    """ As mentioned, this layer can re-range the layer to a certain
    order. It might be useful when the user want to group certain
    layers together.
    The layer take the parameters from a single list, transfered from
    the param string of course.
    For example:
        The given param is [2, 3, 1, 4], the original channel order
        will be re-aranged according to this order.
    NOTE:
        The length of the param list must be equal to the number
        of the bottom channels
    NOTE:
        This layer can have multi bottoms and tops, but the number
        of bottoms and tops must be equal
    """

    def setup(self, bottom, top):
        # Parse the param
        self.param = yaml.load(self.param_str)
        if len(bottom) != len(top):
            raise Exception("""The number of bottom must match with
                            the number of top layers""")
        self.blobs_num = len(bottom)
        # Check if the channels of bottom blob match with the length
        # of the param
        for i in range(self.blobs_num):
            if len(self.param) != bottom[i].shape[1]:
                raise Exception("""The number of channels must be match
with the length of param list""")
        # Reshape the top
        self.reshape(bottom, top)
        self.bottom = bottom
        self.top = top
        # Calc the backward order
        self.param_bp = self.backward_param(self.param)

    def reshape(self, bottom, top):
        for i in range(self.blobs_num):
            top[i].reshape(*bottom[i].shape)

    def backward_param(self, param):
        bp_order = range(len(param))
        for i in range(len(param)):
            bp_order[i] = param.index(i)
        return bp_order

    def forward(self, bottom, top):
        # Swap the channels as the self.param defined
        # First, feed the bottom blobs to top blobs
        for i in range(self.blobs_num):
            top[i].data[...] = bottom[i].data[:, self.param, :, :]

    def backward(self, top, propagate_down, bottom):
        for i in range(self.blobs_num):
            bottom[i].diff[...] = top[i].diff[:, self.param_bp, :, :]
