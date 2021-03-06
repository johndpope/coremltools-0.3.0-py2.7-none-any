# Copyright (c) 2017, Apple Inc. All rights reserved.
#
# Use of this source code is governed by a BSD-3-clause license that can be
# found in the LICENSE.txt file or at https://opensource.org/licenses/BSD-3-Clause

"""
Neural network builder class to construct Core ML models.
"""
from .. import SPECIFICATION_VERSION
from ..proto import Model_pb2 as _Model_pb2
from ..proto import NeuralNetwork_pb2 as _NeuralNetwork_pb2
from ..proto import FeatureTypes_pb2 as _FeatureTypes_pb2
from _interface_management import set_transform_interface_params

import datatypes


def _set_recurrent_activation(param, activation):
    if activation == 'SIGMOID':
        param.sigmoid.MergeFromString('')
    elif activation == 'TANH':
        param.tanh.MergeFromString('')
    elif activation == 'LINEAR':
        param.linear.MergeFromString('')
    elif activation == 'SIGMOID_HARD':
        param.sigmoidHard.MergeFromString('')
    elif activation == 'SCALED_TANH':
        param.scaledTanh.MergeFromString('')
    elif activation == 'RELU':
        param.ReLU.MergeFromString('')
    else:
        raise TypeError("Unsupported activation type with Recurrrent layer: %s." % activation)

class NeuralNetworkBuilder(object):
    """
    Neural network builder class to construct Core ML models.

    The NeuralNetworkBuilder constructs a Core ML neural network specification
    layer by layer. The layers should be added in such an order that the inputs
    to each layer (refered to as blobs) of each layer has been previously
    defined.  The builder can also set pre-processing steps to handle
    specialized input format (e.g. images), and set class labels for neural
    network classifiers.

    Please see the Core ML neural network protobuf message for more information
    on neural network layers, blobs, and parameters.

    Examples
    --------
    .. sourcecode:: python

        # Create a neural network binary classifier that classifies 3-dimensional data points
        # Specify input and output dimensions
        >>> input_dim = (3,)
        >>> output_dim = (2,)

        # Specify input and output features
        >>> input_features = [('data', datatypes.Array(*input_dim)]
        >>> output_features = [('probs', datatypes.Array(*output_dim))]

        # Build a simple neural network with 1 inner product layer
        >>> builder = NeuralNetworkBuilder(input_features, output_features)
        >>> builder.add_inner_product(name = 'ip_layer', W = weights, Wb = bias, nB = 3, nC = 2,
        ... has_bias = True, input_name = 'data', output_name = 'probs')

        # save the spec by the builder
        >>> save_spec(builder.spec, 'network.mlmodel')

    See Also
    --------
    MLModel, datatypes, save_spec
    """

    def __init__(self, input_features, output_features, mode = None):
        """
        Construct a NeuralNetworkBuilder object and set protobuf specification interface.

        Parameters
        ----------
        input_features: [(str, tuple)]
            List of input feature of the network. Each feature is a (name,
            shape) tuple, is the name of the feature, and shape is
            a (d1, d2, ..., dN) tuple that describes the dimensions of the
            input feature.

        output_features: [(str, tuple)]
            List of output feature of the network. Each feature is a (name,
            shape) tuple, where name is the name of the feature, and shape is
            a (d1, d2, ..., dN) tuple that describes the dimensions of the
            output feature.

        mode: str ('classifier', 'regressor' or None)
            Mode (one of 'classifier', 'regressor', or None).

            When mode = 'classifier', a NeuralNetworkClassifier spec will be
            constructed.  When mode = 'regressor', a NeuralNetworkRegressor
            spec will be constructed.

        Examples
        --------
        .. sourcecode:: python

            # Construct a builder that builds a neural network classifier with a 299x299x3
            # dimensional input and 1000 dimensional output
            >>> input_features = [('data', datatypes.Array((299,299,3)))]
            >>> output_features = [('probs', datatypes.Array((1000,)))]
            >>> builder = NeuralNetworkBuilder(input_features, output_features, mode='classifier')

        See Also
        --------
        set_input, set_output, set_class_labels
        """
        # Set the interface params.
        spec = _Model_pb2.Model()
        spec.specificationVersion = SPECIFICATION_VERSION

        # Set inputs and outputs
        spec = set_transform_interface_params(spec, input_features, output_features)

        # Save the spec in the protobuf
        self.spec = spec
        if mode == 'classifier':
            nn_spec = spec.neuralNetworkClassifier
        elif mode == 'regressor':
            nn_spec = spec.neuralNetworkRegressor
        else:
            nn_spec = spec.neuralNetwork
        self.nn_spec = nn_spec

    def set_input(self, input_names, input_dims):
        """
        Set the inputs of the network spec.

        Parameters
        ----------
        input_names: [str]
            List of input names of the network.

        input_dims: [tuple]
            List of input dimensions of the network. The ordering of input_dims
            is the same as input_names.

        Examples
        --------
        .. sourcecode:: python

            # Set the neural network spec inputs to be 3 dimensional vector data1 and
            # 4 dimensional vector data2.
            >>> builder.set_input(input_names = ['data1', 'data2'], [(3,), (4,)])

        See Also
        --------
        set_output, set_class_labels
        """
        spec = self.spec
        nn_spec = self.nn_spec
        for idx, dim in enumerate(input_dims):
            if len(dim) == 3:
                input_shape = (dim[0], dim[1], dim[2])
            elif len(dim) == 2:
                input_shape = (dim[1], )
            elif len(dim) == 1:
                input_shape = tuple(dim)
            else:
                raise RuntimeError("Attempting to add a neural network input with rank " + str(len(dim)) + ". All networks should take inputs of rank 1 or 3.")

            spec.description.input[idx].type.multiArrayType.ClearField("shape")
            spec.description.input[idx].type.multiArrayType.shape.extend(input_shape)

            # TODO: if it's an embedding, this should be integer
            spec.description.input[idx].type.multiArrayType.dataType = _Model_pb2.ArrayFeatureType.DOUBLE

    def set_output(self, output_names, output_dims):
        """
        Set the outputs of the network spec.

        Parameters
        ----------
        output_names: [str]
            List of output names of the network.

        output_dims: [tuple]
            List of output dimensions of the network. The ordering of output_dims is the same
            as output_names.

        Examples
        --------
        .. sourcecode:: python

            # Set the neural network spec outputs to be 3 dimensional vector feature1 and
            # 4 dimensional vector feature2.
            >>> builder.set_output(output_names = ['feature1', 'feature2'], [(3,), (4,)])

        See Also
        --------
        set_input, set_class_labels
        """
        spec = self.spec
        nn_spec = self.nn_spec
        for idx, dim in enumerate(output_dims):
            spec.description.output[idx].type.multiArrayType.ClearField("shape")
            spec.description.output[idx].type.multiArrayType.shape.extend(dim)
            spec.description.output[idx].type.multiArrayType.dataType = _Model_pb2.ArrayFeatureType.DOUBLE

    def set_class_labels(self, class_labels, predicted_feature_name = 'classLabel'):
        """
        Set class labels to the model spec to make it a neural network classifier.

        Parameters
        ----------
        class_labels: list[int or str]
            A list of integers or strings that map the index of the output of a
            neural network to labels in a classifier.

        predicted_feature_name: str
            Name of the output feature for the class labels exposed in the
            Core ML neural network classifier.  Defaults to 'class_output'.

        See Also
        --------
        set_input, set_output, set_pre_processing_parameters
        """
        spec = self.spec
        nn_spec = self.nn_spec

        if len(spec.description.output) == 0:
            raise ValueError(
                "Model should have atleast one output (the probabilities) to automatically make it a classifier.")
        probOutput = spec.description.output[0]
        probOutput.type.dictionaryType.MergeFromString('')
        if len(class_labels) == 0:
            return
        class_type = type(class_labels[0])
        if class_type not in [int, str]:
            raise TypeError("Class labels must be of type Integer or String. (not %s)" % class_type)

        spec.description.predictedProbabilitiesName = probOutput.name
        spec.description.predictedFeatureName = predicted_feature_name

        classLabel = spec.description.output.add()
        classLabel.name = predicted_feature_name
        if class_type == int:
            nn_spec.ClearField('int64ClassLabels')
            probOutput.type.dictionaryType.int64KeyType.MergeFromString('')
            classLabel.type.int64Type.MergeFromString('')
            for c in class_labels:
                nn_spec.int64ClassLabels.vector.append(c)
        else:
            nn_spec.ClearField('stringClassLabels')
            probOutput.type.dictionaryType.stringKeyType.MergeFromString('')
            classLabel.type.stringType.MergeFromString('')
            for c in class_labels:
                nn_spec.stringClassLabels.vector.append(c)

    def add_optionals(self, optionals_in, optionals_out):
        """
        Add optional inputs and outputs to the model spec.

        Parameters
        ----------
        optionals_in: [str]
            List of inputs that are optionals.

        input_dims: [tuple]
            List of outputs that are optionals.

        See Also
        --------
        set_input, set_output

        """
        spec = self.spec
        if (not optionals_in) and (not optionals_out):
            return

        # assuming single sizes here
        input_types = [datatypes.Array(dim) for (name, dim) in optionals_in]
        output_types = [datatypes.Array(dim) for (name, dim) in optionals_out]

        input_names = [str(name) for (name, dim) in optionals_in]
        output_names = [str(name) for (name, dim) in optionals_out]

        input_features = zip(input_names, input_types)
        output_features = zip(output_names, output_types)
       
        len_before_in = len(spec.description.input)
        len_before_out = len(spec.description.output)
       
        # this appends to the existing model interface
        set_transform_interface_params(spec, input_features, output_features, True)
       
        # add types for any extra hidden inputs
        for idx in range(len_before_in, len(spec.description.input)):
            spec.description.input[idx].type.multiArrayType.dataType = _Model_pb2.ArrayFeatureType.DOUBLE
        for idx in range(len_before_out, len(spec.description.output)):
            spec.description.output[idx].type.multiArrayType.dataType = _Model_pb2.ArrayFeatureType.DOUBLE


    def add_inner_product(self, name, W, Wb, nB, nC, has_bias,
                          input_name, output_name):
        """
        Add an inner product layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer
        W: numpy.array
            Weight matrix of shape (nB, nC).
        Wb: numpy.array
            Bias vector of shape (nC, ).
        nB: int
            Number of input channels.
        nC: int
            Number of output channels.
        has_bias: boolean
            Whether the bias vector of this layer is ignored in the spec.
            - If True, the bias vector of this layer is not ignored.
            - If False, the bias vector is ignored.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_embedding, add_convolution
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.innerProduct

        # Fill in the parameters
        spec_layer_params.inputChannels = nB
        spec_layer_params.outputChannels = nC
        spec_layer_params.hasBias = has_bias

        weights = spec_layer_params.weights
        weights.floatValue.extend(map(float, W.flatten()))
        if has_bias:
            bias = spec_layer_params.bias
            bias.floatValue.extend(map(float, Wb.flatten()))

    def add_embedding(self, name, W, Wb, nB, nC, has_bias,
                      input_name, output_name):
        """
        Add an embedding layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer
        W: numpy.array
            Weight matrix of shape (nB, nC).
        Wb: numpy.array
            Bias vector of shape (nC, ).
        nB: int
            Number of input channels.
        nC: int
            Number of output channels.
        has_bias: boolean
            Whether the bias vector of this layer is ignored in the spec.
            - If True, the bias vector of this layer is not ignored.
            - If False, the bias vector is ignored.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_inner_product
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)

        # Fill in the parameters
        spec_layer_params = spec_layer.embedding

        spec_layer_params.inputDim = nB
        spec_layer_params.outputChannels = nC
        spec_layer_params.hasBias = has_bias

        weights = spec_layer_params.weights
        weights.floatValue.extend(map(float, W.flatten()))
        if has_bias:
            bias = spec_layer_params.bias
            bias.floatValue.extend(map(float, Wb.flatten()))


    def add_softmax(self, name, input_name, output_name):
        """
        Add a softmax layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
       
        See Also
        --------
        add_activation, add_inner_product, add_convolution
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.softmax.MergeFromString('')

    def add_activation(self, name, non_linearity, input_name, output_name,
        params=None):
        """
        Add an activation layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer
        non_linearity: str
            The non_linearity (activation) function of this layer. It can be one of the following:

            - 'RELU': Rectified Linear Unit (ReLU) function.
            - 'SIGMOID': sigmoid function.
            - 'TANH': tanh function.
            - 'SCALED_TANH': scaled tanh function, defined as: f(x) = alpha *
              tanh(beta * x) where alpha and beta are constant scalars.
            - 'SOFTPLUS': softplus function.
            - 'SOFTSIGN': softsign function.
            - 'SIGMOID_HARD': hard sigmoid function, defined as: f(x) =
              min(max(alpha * x + beta, -1), 1) where alpha and beta are
              constant scalars.
            - 'LEAKYRELU': leaky relu function, defined as: f(x) = (x >= 0) * x
              + (x < 0) * alpha * x where alpha is a constant scalar.
            - 'PRELU': Parametric ReLU function, defined as: f(x) = (x >= 0) *
              x + (x < 0) * alpha * x
              where alpha is a multi-dimensional array of same size as x.
            - 'ELU': Exponential linear unit function, defined as: f(x) = (x >=
              0) * x + (x < 0) * (alpha * exp(x) - 1) where alpha is a constant
              scalar.
            - 'PARAMETRICSOFTPLUS': Parametric softplus function, defined as:
              f(x) = alpha * log(1 + exp(beta * x)) where alpha and beta are
              two multi-dimensional arrays of same size as x.
            - 'THRESHOLDEDRELU': Thresholded ReLU function, defined as: f(x) =
              (x >= alpha) * x where alpha is a constant scalar.
            - 'LINEAR': linear function.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        params: [float] | [numpy.array]
            Parameters for the activation, depending on non_linearity. When non_linearity is:

            - 'RELU', 'SIGMOID', 'TANH', 'SCALED_TANH', 'SOFTPLUS', 'SOFTSIGN',
              'LINEAR': params is ignored.
            - 'SCALED_TANH', 'SIGMOID_HARD': param is a list of 2 floats
              [alpha, beta].
            - 'LEAKYRELU', 'ELU', 'THRESHOLDEDRELU': param is a list of 1 float
              [alpha].
            - 'PRELU': param is a list of 1 numpy array [alpha]. The shape of
              alpha is (C,), where C is either the number of input channels or
              1. When C = 1, same alpha is applied to all channels.
            - 'PARAMETRICSOFTPLUS': param is a list of 2 numpy arrays [alpha,
              beta]. The shape of alpha and beta is (C, ), where C is either
              the number of input channels or 1. When C = 1, same alpha and
              beta are applied to all channels.

        See Also
        --------
        add_convolution, add_softmax
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.activation

        # Fill in the parameters
        if non_linearity == 'RELU':
            spec_layer_params.ReLU.MergeFromString('')
  
        elif non_linearity == 'SIGMOID':
            spec_layer_params.sigmoid.MergeFromString('')

        elif non_linearity == 'TANH':
            spec_layer_params.tanh.MergeFromString('')

        elif non_linearity == 'SCALED_TANH':
            spec_layer_params.scaledTanh.MergeFromString('')
            if params is None:
                alpha, beta = (0.0, 0.0)
            else:
                alpha, beta = params[0], params[1]
            spec_layer_params.scaledTanh.alpha = alpha
            spec_layer_params.scaledTanh.beta = beta

        elif non_linearity == 'SOFTPLUS':
            spec_layer_params.softplus.MergeFromString('')

        elif non_linearity == 'SOFTSIGN':
            spec_layer_params.softsign.MergeFromString('')

        elif non_linearity == 'SIGMOID_HARD':
            if params is None:
                alpha, beta = (0.2, 0.5)
            else:
                alpha, beta = params[0], params[1]
            spec_layer_params.sigmoidHard.alpha = alpha
            spec_layer_params.sigmoidHard.beta = beta

        elif non_linearity == 'LEAKYRELU':
            if params is None:
                alpha = 0.3
            else:
                alpha = params[0]
            spec_layer_params.leakyReLU.alpha = alpha

        elif non_linearity == 'PRELU':
            # PReLU must provide an np array in params[0]
            spec_layer_params.PReLU.alpha.floatValue.extend(map(float, params.flatten()))

        elif non_linearity == 'ELU':
            # ELU must provide an alpha in params[0]
            spec_layer_params.ELU.alpha = float(params)

        elif non_linearity == 'PARAMETRICSOFTPLUS':
            # Parametric softplus must provide two np arrays for alpha and beta
            alphas, betas = (params[0], params[1])
            # Weight alignment: Keras [H,W,C,F], Espresso [
            spec_layer_params.parametricSoftplus.alpha.floatValue.extend(map(float, alphas.flatten()))
            spec_layer_params.parametricSoftplus.beta.floatValue.extend(map(float, betas.flatten()))
  
        elif non_linearity == 'THRESHOLDEDRELU':
            if params is None:
                theta = 1.0
            else:
                theta = params
            spec_layer_params.thresholdedReLU.alpha = float(theta)
  
        elif non_linearity == 'LINEAR':
            spec_layer_params.linear.MergeFromString('')
        else:
            raise TypeError("Unknown activation type %s." %(non_linearity))

    def add_elementwise(self, name, input_names, output_name, mode):
        """
        Add an element-wise operation layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer
        input_names: list[str]
            A list of input blob names of this layer. The input blobs should have the same shape.
        output_name: str
            The output blob name of this layer.
        mode: str
            A string specifying the mode of the elementwise layer. It can be one of the following:

            - 'CONCAT': concatenate input blobs along the channel axis.
            - 'SEQUENCE_CONCAT': concatenate input blobs along the sequence axis.
            - 'ADD': perform an element-wise summation over the input blobs.
            - 'MULTIPLY': perform an element-wise multiplication over the input blobs.
            - 'DOT': compute the dot product of the two input blobs. In this mode, the length of input_names should be 2.
            - 'COS': compute the cosine similarity of the two input blobs. In this mode, the length of input_names should be 2.
            - 'MAX': compute the element-wise maximum over the input blobs.
            - 'AVE': compute the element-wise average over the input blobs.
       
        See Also
        --------
        add_upsample, add_repeat
       
        """
        spec = self.spec
        nn_spec = self.nn_spec

        spec_layer = nn_spec.layers.add()
        spec_layer.name = name

        for input_name in input_names:
            spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)

        ## Add the following layers.
        if mode == 'CONCAT':
            spec_layer.concat.sequenceConcat = False
        elif mode == 'SEQUENCE_CONCAT':
            spec_layer.concat.sequenceConcat = True
        elif mode == 'ADD':
            spec_layer.add.MergeFromString('')
        elif mode == 'MULTIPLY':
            spec_layer.multiply.MergeFromString('')
        elif mode == 'COS':
            spec_layer.dot.cosineSimilarity = True
        elif mode == 'DOT':
            spec_layer.dot.cosineSimilarity = False
        elif mode == 'MAX':
            spec_layer.max.MergeFromString('')
        elif mode == 'AVE':
            spec_layer.average.MergeFromString('')
        else:
            raise ValueError("Unspported elementwise mode %s" % mode)

    def add_upsample(self, name, scaling_factor_h, scaling_factor_w, input_name, output_name):
        """
        Add upsample layer to the model.
       
        Parameters
        ----------
        name: str
            The name of this layer.
        scaling_factor_h: int
            Scaling factor on the vertical direction.
        scaling_factor_w: int
            Scaling factor on the horizontal direction.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_repeat, add_elementwise
        """
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new inner-product layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.upsample
        spec_layer_params.scalingFactor.append(scaling_factor_h)
        spec_layer_params.scalingFactor.append(scaling_factor_w)

    def add_repeat(self, name, nrep, input_name, output_name):
        """
        Add sequence repeat layer to the model.
       
        Parameters
        ----------
        name: str
            The name of this layer.
        nrep: int
            Number of repetitions of the input blob along the sequence axis.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
       
        See Also
        --------
        add_upsample, add_elementwise
        """
        spec = self.spec
        nn_spec = self.nn_spec
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.sequenceRepeat
        spec_layer_params.nRepetitions = nrep

    def add_convolution(self, name, kernelChannels, outputChannels, height,
            width, stride_height, stride_width, borderMode, groups, W, b,
            has_bias, is_deconv, output_shape, input_name, output_name):
        """
        Add a convolution layer to the network.

        Please see the ConvolutionLayerParams in Core ML neural network
        protobuf message for more information input and output blob dimensions.

        Parameters
        ----------
        name: str
            The name of this layer.
        kernelChannels: int
            Number of channels for the convolution kernels.
        outputChannels: int
            Number of filter kernels. This is equal to the number of channels in the output blob.
        height: int
            Height of each kernel.
        width: int
            Width of each kernel.
        stride_height: int
            Stride along the height direction.
        stride_width: int
            Stride along the height direction.
        borderMode: str
            Option for the output blob shape. Can be either 'valid' or 'same'.
        groups: int
            Number of kernel groups. Each kernel group share the same weights. This is equal to (input channels / kernelChannels).
        W: numpy.array
            Weights of the convolution kernels.
            - If is_deconv is False, W should have shape (outputChannels, kernelChannels, height, width).
            - If is_deconv is True, W should have shape (kernelChannels,outputChannels,kernelHeight,kernelWidth).
        b: numpy.array
            Biases of the convolution kernels. b should have shape (outputChannels, ).
        has_bias: boolean
            Whether bias is ignored.
            - If True, bias is not ignored.
            - If False, bias is ignored.
        is_deconv: boolean
            Whether the convolution layer is performing a convolution or a transposed convolution (deconvolution).
            - If True, the convolution layer is performing transposed convolution.
            - If False, the convolution layer is performing regular convolution.
        output_shape: tuple
            A 3-tuple, specifying the output shape (output_height, output_width, output_channels). Used only when is_deconv == True.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_pooling, add_activation, add_batchnorm
       
        """
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer.convolution.MergeFromString('') # hack to set empty message

        # Set the layer params
        spec_layer_params = spec_layer.convolution
        spec_layer_params.isDeconvolution = is_deconv
        spec_layer_params.outputShape.extend(output_shape)
        spec_layer_params.outputChannels = outputChannels
        spec_layer_params.kernelChannels = kernelChannels
        spec_layer_params.kernelSize.append(height)
        spec_layer_params.kernelSize.append(width)
        spec_layer_params.stride.append(stride_height)
        spec_layer_params.stride.append(stride_width)

        if borderMode == 'valid':
            valid = spec_layer_params.valid
            height_border = spec_layer_params.valid.paddingAmounts.borderAmounts.add()
            height_border.startEdgeSize = 0
            height_border.endEdgeSize = 0
            width_border = spec_layer_params.valid.paddingAmounts.borderAmounts.add()
            width_border.startEdgeSize = 0
            width_border.endEdgeSize = 0
        elif borderMode == 'same':
            same = spec_layer_params.same
            spec_layer_params.same.asymmetryMode = _NeuralNetwork_pb2.SamePadding.SamePaddingMode.Value('BOTTOM_RIGHT_HEAVY')
        else:
            raise NotImplementedError(
                'Border mode %s is not implemented.' % borderMode)

        spec_layer_params.nGroups = groups
        spec_layer_params.hasBias = has_bias

        # Assign weights
        weights = spec_layer_params.weights

        # Weight alignment: Keras [H,W,C,F], Espresso: [F,C,H,W], if conv; [C,F,H,W], if deconv
        if not is_deconv:
            Wt = W.transpose((3,2,0,1)).flatten()
        else:
            Wt = W.transpose((2,3,0,1)).flatten()
        for idx in xrange(outputChannels * kernelChannels * height * width):
            weights.floatValue.append(float(Wt[idx]))

        # Assign biases
        if has_bias:
            bias = spec_layer_params.bias
            for f in xrange(outputChannels):
                bias.floatValue.append(float(b[f]))

    def add_pooling(self, name, height, width, stride_height, stride_width,
            layer_type, padding_type, exclude_pad_area, is_global, input_name, output_name):
        """
        Add a pooling layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        height: int
            Height of pooling region.
        width: int
            Number of elements to be padded on the right side of the input blob.
        stride_height: int
            Stride along the height direction.
        stride_width: int
            Stride along the height direction.
        layer_type: str
            Type of pooling performed. Can either be 'MAX', 'AVERAGE' or 'L2'.
        padding_type: str
            Option for the output blob shape. Can be either 'VALID' or 'SAME'.
        exclude_pad_area: boolean
            Whether to exclude padded area in the pooling operation.
            - If True, the value of the padded area will be excluded.
            - If False, the padded area will be included.
            This flag is only used with average pooling.
        is_global: boolean
            Whether the pooling operation is global.
            - If True, the pooling operation is global -- the pooling region is of the same size of the input blob.
            Parameters height, width, stride_height, stride_width will be ignored.
            - If False, the pooling operation is not global.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_convolution, add_pooling, add_activation
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.pooling

        # Set the parameters
        spec_layer_params.type = \
                    _NeuralNetwork_pb2.PoolingLayerParams.PoolingType.Value(layer_type)

        if padding_type == 'VALID':
            height_border = spec_layer_params.valid.paddingAmounts.borderAmounts.add()
            height_border.startEdgeSize = 0
            height_border.endEdgeSize = 0
            width_border = spec_layer_params.valid.paddingAmounts.borderAmounts.add()
            width_border.startEdgeSize = 0
            width_border.endEdgeSize = 0
        elif padding_type == 'SAME':
            spec_layer_params.same.asymmetryMode = _NeuralNetwork_pb2.SamePadding.SamePaddingMode.Value('BOTTOM_RIGHT_HEAVY')

        spec_layer_params.kernelSize.append(height)
        spec_layer_params.kernelSize.append(width)
        spec_layer_params.stride.append(stride_height)
        spec_layer_params.stride.append(stride_width)
        spec_layer_params.avgPoolExcludePadding = exclude_pad_area
        spec_layer_params.globalPooling = is_global

    def add_padding(self, name, left, right, top, bottom, value, input_name,
            output_name):
        """
        Add a padding layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        left: int
            Number of elements to be padded on the left side of the input blob.
        right: int
            Number of elements to be padded on the right side of the input blob.
        top: int
            Number of elements to be padded on the top of the input blob.
        bottom: int
            Number of elements to be padded on the bottom of the input blob.
        value: float
            Value of the elements padded.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_crop, add_convolution, add_pooling
        """
        # Currently only constant padding is supported.
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.padding

        # Set the parameters
        spec_layer_params.constant.value = value
        height_border = spec_layer_params.paddingAmounts.borderAmounts.add()
        height_border.startEdgeSize = top
        height_border.endEdgeSize = bottom
        width_border = spec_layer_params.paddingAmounts.borderAmounts.add()
        width_border.startEdgeSize = left
        width_border.endEdgeSize = right

    def add_crop(self, name, left, right, top, bottom, offset, input_name,
            output_name):
        """
        Add a cropping layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        left: int
            Number of elements to be cropped on the left side of the input blob when the crop layer takes 1 input.
            When the crop layer takes 2 inputs, this parameter is ignored.
        right: int
            Number of elements to be cropped on the right side of the input blob when the crop layer takes 1 input.
            When the crop layer takes 2 inputs, this parameter is ignored.
        top: int
            Number of elements to be cropped on the top of the input blob When the crop layer takes 1 input.
            When the crop layer takes 2 inputs, this parameter is ignored.
        bottom: int
            Number of elements to be cropped on the bottom of the input blob when the crop layer takes 1 input.
            When the crop layer takes 2 inputs, this parameter is ignored.
        offset: (int, int)
            Offset along the height and width directions when the crop layer takes 2 inputs.
            When the crop layer takes 1 input, this parameter is ignored.
        input_names: str | list(str)
            The input blob name(s) of this layer. Must be either a string, a list of 1 string (1 input crop layer),
            or a list of 2 strings (2-input crop layer).
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_padding, add_convolution, add_pooling
        """
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.crop

        # Set the parameters
        spec_layer_params.offset.extend(offset)
        height_border = spec_layer_params.cropAmounts.borderAmounts.add()
        height_border.startEdgeSize = top
        height_border.endEdgeSize = bottom
        width_border = spec_layer_params.cropAmounts.borderAmounts.add()
        width_border.startEdgeSize = left
        width_border.endEdgeSize = right

    def add_vanilla_rnn(self,name, W_h, W_x, b, activation, hidden_size, input_size, input_names, output_names, output_all = False, reverse_input = False):
        """
        Add a simple recurrent layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        W_h: numpy.array
            Weights of the recurrent layer's hidden state. Must be of shape (hidden_size, hidden_size).
        W_x: numpy.array
            Weights of the recurrent layer's input. Must be of shape (hidden_size, input_size).
        b: numpy.array
            Bias of the recurrent layer's output. Must be of shape (hidden_size, ).
        activation: str
            Activation function name. Can be one of the following option:
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
            See add_activation for more detailed description.
        hidden_size: int
            Number of hidden units. This is equal to the number of channels of output shape.
        input_size: int
            Number of the number of channels of input shape.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        output_all: boolean
            Whether the recurrent layer should output at every time step.
            - If False, the output is the result after the final state update.
            - If True, the output is a sequence, containing outputs at all time steps.
        reverse_input: boolean
            Whether the recurrent layer should process the input sequence in the reverse order.
            - If False, the input sequence order is not reversed.
            - If True, the input sequence order is reversed.

        See Also
        --------
        add_activation, add_gru, add_unilstm, add_bidirlstm
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new Layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        for name in input_names:
            spec_layer.input.append(name)
        for name in output_names:
            spec_layer.output.append(name)
        spec_layer_params = spec_layer.simpleRecurrent
        spec_layer_params.reverseInput = reverse_input

        #set the parameters
        spec_layer_params.inputVectorSize = input_size
        spec_layer_params.outputVectorSize = hidden_size
        if b is not None and b.any():
            spec_layer_params.hasBiasVector = True
        spec_layer_params.sequenceOutput = output_all

        activation_f = spec_layer_params.activation
        _set_recurrent_activation(activation_f, activation)

        # Write the weights
        spec_layer_params.weightMatrix.floatValue.extend(map(float, W_x.flatten()))
        spec_layer_params.recursionMatrix.floatValue.extend(map(float, W_h.flatten()))

        if b is not None and b.any():
            spec_layer_params.biasVector.floatValue.extend(map(float, b.flatten()))

    def add_gru(self, name, W_h, W_x, b, activation, inner_activation,
            hidden_size, input_size, input_names, output_names,
            output_all = False, reverse_input = False):
        """
        Add a Gated-Recurrent Unit (GRU) layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        W_h: [numpy.array]
            List of recursion weight matrices. The ordering is [R_z, R_r, R_o],
            where R_z, R_r and R_o are weight matrices at update gate, reset gate and output gate.
            The shapes of these matrices are (hidden_size, hidden_size).
        W_x: [numpy.array]
            List of input weight matrices. The ordering is [W_z, W_r, W_o],
            where W_z, W_r, and W_o are weight matrices at update gate, reset gate and output gate.
            The shapes of these matrices are (hidden_size, input_size).
        b: [numpy.array]
            List of biases of the GRU layer. The ordering is [b_z, b_r, b_o],
            where b_z, b_r, b_o are biases at update gate, reset gate and output gate.
            The shapes of the biases are (hidden_size, ).
        activation: str
            Activation function used at the output gate. Can be one of the following option:
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
            See add_activation for more detailed description.
        inner_activation: str
            Inner activation function used at update and reset gates. Can be one of the following option:
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
            See add_activation for more detailed description.
        hidden_size: int
            Number of hidden units. This is equal to the number of channels of output shape.
        input_size: int
            Number of the number of channels of input shape.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        output_all: boolean
            Whether the recurrent layer should output at every time step.
            - If False, the output is the result after the final state update.
            - If True, the output is a sequence, containing outputs at all time steps.
        reverse_input: boolean
            Whether the recurrent layer should process the input sequence in the reverse order.
            - If False, the input sequence order is not reversed.
            - If True, the input sequence order is reversed.

        See Also
        --------
        add_activation, add_vanilla_rnn, add_unilstm, add_bidirlstm
        """
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new Layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
  
        for name in input_names:
            spec_layer.input.append(name)
        for name in output_names:
            spec_layer.output.append(name)
        spec_layer_params = spec_layer.gru

        # set the parameters
        spec_layer_params.inputVectorSize = input_size
        spec_layer_params.outputVectorSize = hidden_size
        if b is not None and b.any():
            spec_layer_params.hasBiasVectors = True
        spec_layer_params.sequenceOutput = output_all
        spec_layer_params.reverseInput = reverse_input

        activation_f = spec_layer_params.activations.add()
        activation_g = spec_layer_params.activations.add()
        _set_recurrent_activation(activation_f, inner_activation)
        _set_recurrent_activation(activation_g, activation)

        # Write the weights
        spec_layer_params.updateGateWeightMatrix.floatValue.extend(map(float, W_x[0,0, 0 * hidden_size:1 * hidden_size,:].flatten()))
        spec_layer_params.resetGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        spec_layer_params.outputGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))

        spec_layer_params.updateGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 0 * hidden_size:1 * hidden_size, :].flatten()))
        spec_layer_params.resetGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        spec_layer_params.outputGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))

        if b is not None and b.any():
            spec_layer_params.updateGateBiasVector.floatValue.extend(map(float, b[0 * hidden_size:1 * hidden_size].flatten()))
            spec_layer_params.resetGateBiasVector.floatValue.extend(map(float, b[1 * hidden_size:2 * hidden_size].flatten()))
            spec_layer_params.outputGateBiasVector.floatValue.extend(map(float, b[2 * hidden_size:3 * hidden_size].flatten()))

    def add_unilstm(self, name, hidden_size, input_size, input_names, output_names,
                    W_h, W_x,
                    inner_activation = 'SIGMOID',
                    cell_state_update_activation = 'TANH',
                    output_activation = 'TANH',
                    b = None,
                    peep = None,
                    output_all = False,
                    forget_bias = False, coupled_input_forget_gate = False,
                    cell_clip_threshold = 50.0, reverse_input = False):
        """
        Add a Uni-directional LSTM layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        hidden_size: int
            Number of hidden units. This is equal to the number of channels of output shape.
        input_size: int
            Number of the number of channels of input shape.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        W_h: [numpy.array]
            List of recursion weight matrices. The ordering is [R_i, R_f, R_z, R_o],
            where R_i, R_f, R_z, R_o are weight matrices at input gate, forget gate, cell gate and output gate.
            The shapes of these matrices are (hidden_size, hidden_size).
        W_x: [numpy.array]
            List of input weight matrices. The ordering is [W_i, W_f, W_z, W_o],
            where W_i, W_f, W_z, W_o are weight matrices at input gate, forget gate, cell gate and output gate.
            The shapes of these matrices are (hidden_size, input_size).
        b: [numpy.array]
            List of biases. The ordering is [b_i, b_f, b_z, b_o],
            where b_i, b_f, b_z, b_o are biases at input gate, forget gate, cell gate and output gate.
            The shapes of the biases (hidden_size).
        inner_activation: str
            Inner activation function used at input and forget gate. Can be one of the following option:
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
        cell_state_update_activation: str
            Cell state update activation function used at the cell state update gate.
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
        output_activation: str
            Activation function used at the output gate. Can be one of the following option:
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
        peep: [numpy.array] | None
            List of peephole vectors. The ordering is [p_i, p_f, p_o],
            where p_i, p_f, and p_o are peephole vectors at input gate, forget gate, output gate.
            The shapes of the peephole vectors are (hidden_size,).
        output_all: boolean
            Whether the LSTM layer should output at every time step.
            - If False, the output is the result after the final state update.
            - If True, the output is a sequence, containing outputs at all time steps.
        forget_bias: boolean
            If True, a vector of 1s is added to forget gate bias.
        coupled_input_forget_gate : boolean
            If True, the inpute gate and forget gate is coupled. i.e. forget gate is not used.
        cell_clip_threshold : float
            The limit on the maximum and minimum values on the cell state.
            If not provided, it is defaulted to 50.0.
        reverse_input: boolean
            Whether the LSTM layer should process the input sequence in the reverse order.
            - If False, the input sequence order is not reversed.
            - If True, the input sequence order is reversed.

        See Also
        --------
        add_activation, add_vanilla_rnn, add_gru, add_bidirlstm
        """
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new Layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        for name in input_names:
            spec_layer.input.append(name)
        for name in output_names:
            spec_layer.output.append(name)
        spec_layer_params = spec_layer.uniDirectionalLSTM
        params = spec_layer_params.params
        weight_params = spec_layer_params.weightParams

        # set the parameters
        spec_layer_params.inputVectorSize = input_size
        spec_layer_params.outputVectorSize = hidden_size
        params.sequenceOutput = output_all
        params.forgetBias = False
        if b is not None and b.any():
            params.hasBiasVectors = True
        if peep is not None and peep.any():
            params.hasPeepholeVectors = True
        params.coupledInputAndForgetGate = coupled_input_forget_gate
        params.cellClipThreshold = cell_clip_threshold
        params.forgetBias = forget_bias

        spec_layer_params.reverseInput = reverse_input

        activation_f = spec_layer_params.activations.add()
        activation_g = spec_layer_params.activations.add()
        activation_h = spec_layer_params.activations.add()
        _set_recurrent_activation(activation_f, inner_activation)
        _set_recurrent_activation(activation_g, cell_state_update_activation)
        _set_recurrent_activation(activation_h, output_activation)

        # Write the weights
        weight_params.inputGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 0 * hidden_size:1 * hidden_size, :].flatten()))
        weight_params.forgetGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        weight_params.outputGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))
        weight_params.blockInputWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 3 * hidden_size:4 * hidden_size, :].flatten()))

        weight_params.inputGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 0 * hidden_size:1 * hidden_size, :].flatten()))
        weight_params.forgetGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        weight_params.outputGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))
        weight_params.blockInputRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 3 * hidden_size:4 * hidden_size, :].flatten()))

        if b is not None and b.any():
            weight_params.inputGateBiasVector.floatValue.extend(map(float, b[0 * hidden_size:1 * hidden_size].flatten()))
            weight_params.forgetGateBiasVector.floatValue.extend(map(float, b[1 * hidden_size:2 * hidden_size].flatten()))
            weight_params.outputGateBiasVector.floatValue.extend(map(float, b[2 * hidden_size:3 * hidden_size].flatten()))
            weight_params.blockInputBiasVector.floatValue.extend(map(float, b[3 * hidden_size:4 * hidden_size].flatten()))

        if peep is not None and peep.any():
            weight_params.inputGatePeepholeVector.floatValue.extend(map(float, peep[0 * hidden_size:1 * hidden_size].flatten()))
            weight_params.forgetGatePeepholeVector.floatValue.extend(map(float, peep[1 * hidden_size:2 * hidden_size].flatten()))
            weight_params.outputGatePeepholeVector.floatValue.extend(map(float, peep[2 * hidden_size:3 * hidden_size].flatten()))

    def add_bidirlstm(self, name, hidden_size, input_size, input_names, output_names,
            W_h, W_x, W_h_back, W_x_back,
            inner_activation = 'SIGMOID',
            cell_state_update_activation = 'TANH',
            output_activation = 'TANH',
            b = None, b_back = None,
            peep = None, peep_back = None,
            output_all = False,
            forget_bias = False, coupled_input_forget_gate= False, cell_clip_threshold = 50.0):

        """
        Add a Bi-directional LSTM layer to the model.

        Parameters
        ----------
        name: str
            The name of this layer.
        hidden_size: int
            Number of hidden units. This is equal to the number of channels of output shape.
        input_size: int
            Number of the number of channels of input shape.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        W_h: [numpy.array]
            List of recursion weight matrices for the forward layer. The ordering is [R_i, R_f, R_z, R_o],
            where R_i, R_f, R_z, R_o are weight matrices at input gate, forget gate, cell gate and output gate.
            The shapes of these matrices are (hidden_size, hidden_size).
        W_x: [numpy.array]
            List of input weight matrices for the forward layer. The ordering is [W_i, W_f, W_z, W_o],
            where W_i, W_f, W_z, W_o are weight matrices at input gate, forget gate, cell gate and output gate.
            The shapes of these matrices are (hidden_size, input_size).
        W_h_back: [numpy.array]
            List of recursion weight matrices for the backward layer. The ordering is [R_i, R_f, R_z, R_o],
            where R_i, R_f, R_z, R_o are weight matrices at input gate, forget gate, cell gate and output gate.
            The shapes of these matrices are (hidden_size, hidden_size).
        W_x_back: [numpy.array]
            List of input weight matrices for the backward layer. The ordering is [W_i, W_f, W_z, W_o],
            where W_i, W_f, W_z, W_o are weight matrices at input gate, forget gate, cell gate and output gate.
            The shapes of these matrices are (hidden_size, input_size).
        inner_activation: str
            Inner activation function used at input and forget gate. Can be one of the following option:
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
        cell_state_update_activation: str
            Cell state update activation function used at the cell state update gate.
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
        output_activation: str
            Activation function used at the output gate. Can be one of the following option:
            ['RELU', 'TANH', 'SIGMOID', 'SCALED_TANH', 'SIGMOID_HARD', 'LINEAR'].
        b: [numpy.array]
            List of biases for the forward layer. The ordering is [b_i, b_f, b_z, b_o],
            where b_i, b_f, b_z, b_o are biases at input gate, forget gate, cell gate and output gate.
            The shapes of the biases (hidden_size).
        b_back: [numpy.array]
            List of biases for the backward layer. The ordering is [b_i, b_f, b_z, b_o],
            where b_i, b_f, b_z, b_o are biases at input gate, forget gate, cell gate and output gate.
            The shapes of the biases (hidden_size).
        peep: [numpy.array] | None
            List of peephole vectors for the forward layer. The ordering is [p_i, p_f, p_o],
            where p_i, p_f, and p_o are peephole vectors at input gate, forget gate, output gate.
            The shapes of the peephole vectors are (hidden_size,).
        peep_back: [numpy.array] | None
            List of peephole vectors for the backward layer. The ordering is [p_i, p_f, p_o],
            where p_i, p_f, and p_o are peephole vectors at input gate, forget gate, output gate.
            The shapes of the peephole vectors are (hidden_size,).
        output_all: boolean
            Whether the LSTM layer should output at every time step.
            - If False, the output is the result after the final state update.
            - If True, the output is a sequence, containing outputs at all time steps.
        forget_bias: boolean
            If True, a vector of 1s is added to forget gate bias.
        coupled_input_forget_gate : boolean
            If True, the inpute gate and forget gate is coupled. i.e. forget gate is not used.
        cell_clip_threshold : float
            The limit on the maximum and minimum values on the cell state.
            If not provided, it is defaulted to 50.0.

        See Also
        --------
        add_activation, add_vanilla_rnn, add_unilstm, add_bidirlstm
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new Layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        for name in input_names:
            spec_layer.input.append(name)
        for name in output_names:
            spec_layer.output.append(name)
        spec_layer_params = spec_layer.biDirectionalLSTM
        params = spec_layer_params.params
        weight_params = spec_layer_params.weightParams.add()
        weight_params_back = spec_layer_params.weightParams.add()

        # set the parameters
        spec_layer_params.inputVectorSize = input_size
        spec_layer_params.outputVectorSize = hidden_size
        if b is not None and b.any():
            params.hasBiasVectors = True
        params.sequenceOutput = output_all
        params.forgetBias = forget_bias
        if peep is not None and peep.any():
            params.hasPeepholeVectors = True
        params.coupledInputAndForgetGate = coupled_input_forget_gate
        params.cellClipThreshold = cell_clip_threshold

        #set activations
        activation_f = spec_layer_params.activationsForwardLSTM.add()
        activation_g = spec_layer_params.activationsForwardLSTM.add()
        activation_h = spec_layer_params.activationsForwardLSTM.add()
        _set_recurrent_activation(activation_f, inner_activation)
        _set_recurrent_activation(activation_g, cell_state_update_activation)
        _set_recurrent_activation(activation_h, output_activation)

        activation_f_back = spec_layer_params.activationsBackwardLSTM.add()
        activation_g_back = spec_layer_params.activationsBackwardLSTM.add()
        activation_h_back = spec_layer_params.activationsBackwardLSTM.add()
        _set_recurrent_activation(activation_f_back, inner_activation)
        _set_recurrent_activation(activation_g_back, cell_state_update_activation)
        _set_recurrent_activation(activation_h_back, output_activation)


        # Write the forward lstm weights
        weight_params.inputGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 0 * hidden_size:1 * hidden_size, :].flatten()))
        weight_params.forgetGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        weight_params.outputGateWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))
        weight_params.blockInputWeightMatrix.floatValue.extend(map(float, W_x[0, 0, 3 * hidden_size:4 * hidden_size, :].flatten()))

        weight_params.inputGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 0 * hidden_size:1 * hidden_size, :].flatten()))
        weight_params.forgetGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        weight_params.outputGateRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))
        weight_params.blockInputRecursionMatrix.floatValue.extend(map(float, W_h[0, 0, 3 * hidden_size:4 * hidden_size, :].flatten()))

        if b is not None and b.any():
            weight_params.inputGateBiasVector.floatValue.extend(map(float, b[0 * hidden_size:1 * hidden_size].flatten()))
            weight_params.forgetGateBiasVector.floatValue.extend(map(float, b[1 * hidden_size:2 * hidden_size].flatten()))
            weight_params.outputGateBiasVector.floatValue.extend(map(float, b[2 * hidden_size:3 * hidden_size].flatten()))
            weight_params.blockInputBiasVector.floatValue.extend(map(float, b[3 * hidden_size:4 * hidden_size].flatten()))

        if peep is not None and peep.any():
            weight_params.inputGatePeepholeVector.floatValue.extend(map(float, peep[0 * hidden_size:1 * hidden_size].flatten()))
            weight_params.forgetGatePeepholeVector.floatValue.extend(map(float, peep[1 * hidden_size:2 * hidden_size].flatten()))
            weight_params.outputGatePeepholeVector.floatValue.extend(map(float, peep[2 * hidden_size:3 * hidden_size].flatten()))


        # Write the backward lstm weights
        weight_params_back.inputGateWeightMatrix.floatValue.extend(map(float, W_x_back[0, 0, 0 * hidden_size:1 * hidden_size, :].flatten()))
        weight_params_back.forgetGateWeightMatrix.floatValue.extend(map(float, W_x_back[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        weight_params_back.outputGateWeightMatrix.floatValue.extend(map(float, W_x_back[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))
        weight_params_back.blockInputWeightMatrix.floatValue.extend(map(float, W_x_back[0, 0, 3 * hidden_size:4 * hidden_size, :].flatten()))

        weight_params_back.inputGateRecursionMatrix.floatValue.extend(map(float, W_h_back[0, 0, 0 * hidden_size:1 * hidden_size, :].flatten()))
        weight_params_back.forgetGateRecursionMatrix.floatValue.extend(map(float, W_h_back[0, 0, 1 * hidden_size:2 * hidden_size, :].flatten()))
        weight_params_back.outputGateRecursionMatrix.floatValue.extend(map(float, W_h_back[0, 0, 2 * hidden_size:3 * hidden_size, :].flatten()))
        weight_params_back.blockInputRecursionMatrix.floatValue.extend(map(float, W_h_back[0, 0, 3 * hidden_size:4 * hidden_size, :].flatten()))

        if b is not None and b.any():
            weight_params_back.inputGateBiasVector.floatValue.extend(map(float, b_back[0 * hidden_size:1 * hidden_size].flatten()))
            weight_params_back.forgetGateBiasVector.floatValue.extend(map(float, b_back[1 * hidden_size:2 * hidden_size].flatten()))
            weight_params_back.outputGateBiasVector.floatValue.extend(map(float, b_back[2 * hidden_size:3 * hidden_size].flatten()))
            weight_params_back.blockInputBiasVector.floatValue.extend(map(float, b_back[3 * hidden_size:4 * hidden_size].flatten()))

        if peep_back is not None and peep_back.any():
            weight_params_back.inputGatePeepholeVector.floatValue.extend(map(float, peep_back[0 * hidden_size:1 * hidden_size].flatten()))
            weight_params_back.forgetGatePeepholeVector.floatValue.extend(map(float, peep_back[1 * hidden_size:2 * hidden_size].flatten()))
            weight_params_back.outputGatePeepholeVector.floatValue.extend(map(float, peep_back[2 * hidden_size:3 * hidden_size].flatten()))


    def add_flatten(self, mode, name, input_name, output_name):
        """
        Add a flatten layer.

        Parameters
        ----------
        name: str
            The name of this layer.
        mode: int
            If mode == 0, the flatten layer is in CHANNEL_FIRST mode.
            If mode == 1, the flatten layer is in CHANNEL_LAST mode.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.

        See Also
        --------
        add_permute, add_reshape
        """
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)
        spec_layer_params = spec_layer.flatten

        # Set the parameters
        if mode == 0:
            spec_layer_params.mode = \
                        _NeuralNetwork_pb2.FlattenLayerParams.FlattenOrder.Value('CHANNEL_FIRST')
        elif mode == 1:
            spec_layer_params.mode = \
                        _NeuralNetwork_pb2.FlattenLayerParams.FlattenOrder.Value('CHANNEL_LAST')
        else:
            raise NotImplementedError(
                'Unknown flatten mode %d ' % mode)

    def add_batchnorm(self, name, channels, gamma, beta, mean, variance, input_name,
                      output_name, epsilon = 1e-5, computeMeanVar = False, instanceNormalization = False):
        """
        Add a Batch Normalization layer. Batch Normalization operation is
        defined as: y = gamma * (x - mean) / sqrt(variance + epsilon) + beta

        Parameters
        ----------
        name: str
            The name of this layer.
        channels: int
            Number of channels of the input blob.
        gamma: numpy.array
            Values of gamma. Must be numpy array of shape (channels, ).
        beta: numpy.array
            Values of beta. Must be numpy array of shape (channels, ).
        mean: numpy.array
            Means of the input blob on each channel. Must be numpy array of shape (channels, ).
        variance:
            Variances of the input blob on each channel. Must be numpy array of shape (channels, ).
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        epsilon: float
            Value of epsilon. Defaults to 1e-5 if not specified.
        computeMeanVar: boolean
            Defaults to False.

            - If True, the mean and variance of input blob is computed on the
              fly, and parameters mean and variance are ignored.
            - If False, the mean and variance of input blob is set to provided
              values of mean and variance, and the parameter
              instanceNormalization is ignored.

        instanceNormalization: boolean
            When computeMeanVar is False, this flag is ignored.

            - If True, the mean and variance of input blob is computed for every single input instance.
            - If False, the mean and variance is computed for the whole batch.

        See Also
        --------
        add_convolution, add_pooling, add_inner_product
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)

        spec_layer_params = spec_layer.batchnorm

        # Set the parameters
        spec_layer_params.channels = channels
        spec_layer_params.gamma.floatValue.extend(map(float, gamma.flatten()))
        spec_layer_params.beta.floatValue.extend(map(float, beta.flatten()))
        spec_layer_params.mean.floatValue.extend(map(float, mean.flatten()))
        spec_layer_params.variance.floatValue.extend(map(float, variance.flatten()))
        spec_layer_params.epsilon = epsilon
        spec_layer_params.computeMeanVar = computeMeanVar
        spec_layer_params.instanceNormalization = instanceNormalization


    def add_permute(self, name, input_name, output_name, dim):
        """
        Add a permute layer.

        Parameters
        ----------
        name: str
            The name of this layer.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        dim: tuple
            Dimension of the output blob. The product of dim must be equal to
            the shape of the input blob.

        See Also
        --------
        add_flatten, add_reshape
        """
        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)

        spec_layer_params = spec_layer.permute
        spec_layer_params.axis.extend(list(dim))

    def add_reshape(self, name, input_name, output_name, target_shape, mode):
        """
        Add a reshape layer.

        Parameters
        ----------
        name: str
            The name of this layer.
        input_name: str
            The input blob name of this layer.
        output_name: str
            The output blob name of this layer.
        target_shape: tuple
            Shape of the output blob. The product of target_shape must be equal
            to the shape of the input blob.
        mode: int
            - If mode == 0, the reshape layer is in CHANNEL_FIRST mode.
            - If mode == 1, the reshape layer is in CHANNEL_LAST mode.

        See Also
        --------
        add_flatten, add_permute
        """

        spec = self.spec
        nn_spec = self.nn_spec

        # Add a new layer
        spec_layer = nn_spec.layers.add()
        spec_layer.name = name
        spec_layer.input.append(input_name)
        spec_layer.output.append(output_name)

        spec_layer_params = spec_layer.reshape
        spec_layer_params.targetShape.extend(target_shape)
        if mode == 0:
            spec_layer_params.mode = \
                    _NeuralNetwork_pb2.ReshapeLayerParams.ReshapeOrder.Value('CHANNEL_FIRST')
        else:
            spec_layer_params.mode = \
                    _NeuralNetwork_pb2.ReshapeLayerParams.ReshapeOrder.Value('CHANNEL_LAST')


    def add_dropout(self, name, input_name, output_name):
        pass


    def set_pre_processing_parameters(self, image_input_names = [], is_bgr = False,
            red_bias = 0.0, green_bias = 0.0, blue_bias = 0.0, gray_bias = 0.0, image_scale = 1.0):
        """Add pre-processing parameters to the neural network object

        Parameters
        ----------
        image_input_names: [str]
            Name if input blobs that are images

        is_bgr: bool
            Image pixel order (RGB or BGR)

        red_bias: float
            Image re-centering parameter (red channel)

        blue_bias: float
            Image re-centering parameter (blue channel)

        green_bias: float
            Image re-centering parameter (green channel)

        image_scale: float
            Value by which to scale the images.

        See Also
        --------
        set_input, set_output, set_class_labels
        """
        spec = self.spec
        if image_input_names:
            preprocessing = self.nn_spec.preprocessing.add()
        else:
            return # nothing to do here
        # Add image inputs
        for input_ in spec.description.input:
            if input_.name in image_input_names:
                if input_.type.WhichOneof('Type') == 'multiArrayType':
                    array_shape = tuple(input_.type.multiArrayType.shape)
                    channels, height, width = array_shape
                    if channels == 1:
                        input_.type.imageType.colorSpace = _FeatureTypes_pb2.ImageFeatureType.ColorSpace.Value('GRAYSCALE')
                    elif channels == 3:
                        if is_bgr:
                            input_.type.imageType.colorSpace = _FeatureTypes_pb2.ImageFeatureType.ColorSpace.Value('BGR')
                        else:
                            input_.type.imageType.colorSpace = _FeatureTypes_pb2.ImageFeatureType.ColorSpace.Value('RGB')
                    else:
                        raise ValueError("Channel Value %d not supported for image inputs" % channels)
                    input_.type.imageType.width = width
                    input_.type.imageType.height = height

        # Add image pre-processing
        scaler = preprocessing.scaler
        scaler.channelScale = image_scale
        scaler.redBias = red_bias
        scaler.blueBias = blue_bias
        scaler.greenBias = green_bias
        scaler.grayBias = gray_bias
