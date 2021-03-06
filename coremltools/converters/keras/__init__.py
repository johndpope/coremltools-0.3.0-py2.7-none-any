# Copyright (c) 2017, Apple Inc. All rights reserved.
#
# Use of this source code is governed by a BSD-3-clause license that can be
# found in the LICENSE.txt file or at https://opensource.org/licenses/BSD-3-Clause

from ..._deps import HAS_KERAS_TF as _HAS_KERAS_TF

if _HAS_KERAS_TF:
    import keras as _keras
    import logging as _logging
    if _keras.backend.backend() != 'tensorflow':
        _HAS_KERAS_TF = False
        _logging.warn('Currently, only Keras models with TensorFlow backend can be converted to CoreML.')

from ._keras_converter import convert
