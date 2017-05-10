#!/usr/bin/python

# This module calc the surface normal map from the depth map

import glog as log
import numpy as np


def calc_surface_normal_map(dep, focal, radius, resize=None, mask=None):
    """
    This function calc the surface normal map according to the depth map
    focal:      The pixel wise virtual focal length
    radius:     The radius to calc the surface normal
    resize:     [height, width] the resolution of the output surface normal map
                which will save computation time
    mask:       If set, only true pixel should be used to calc normal value
    """
    if resize is None:
        normal = np.zeros([dep.shape[0], dep.shape[1], 3])
    else:
        if len(resize) != 2:
            log.error('ERROR: The resize parameter should be [height, width]')
            return None
        normal = np.zeros([resize[0], resize[1], 3])
    if mask is not None:
        if mask.shape[0] != dep.shape[0] or mask.shape[1] != dep.shape[1]:
            log.error('ERROR: The size of the mask not match with the size \
of the dep: %s vs %s' % (str(mask.shape), str(dep.shape)))
            return None

    # Generate the kernel
    kernel = _gen_kernel(radius)
    # Iter the pixels of the surface normal map
    for h in range(normal.shape[0]):
        _gen_row(dep, normal, mask, h, kernel, focal, resize)

    return normal


def _gen_row(dep, normal, mask, h, kernel, focal, resize):
    """
    This function generate the surface normal of a raw, which is used
    for the multi thread function
    """
    for w in range(normal.shape[1]):
        # Get the coord on depth map
        if resize is None:
            dep_coord = [h, w]
        else:
            dep_coord = _map_coord(normal.shape, dep.shape, [h, w])
        # Get the point list within the radius
        point_list = \
            _get_point_list(dep.shape, dep_coord, kernel, mask)
        if len(point_list) == 0:
            x = 0
            y = 0
            z = 1
        else:
            # Calc the x gradient and the y gradient
            x_gradient, y_gradient = \
                _calc_gradient(dep, point_list, [h, w], focal)

            z = 1.0
            x = - x_gradient * z
            y = - y_gradient * z

            x, y, z = _normalize(x, y, z)

        normal[h, w, 0] = x
        normal[h, w, 1] = y
        normal[h, w, 2] = z


def _map_coord(src_shape, dst_shape, coord):
    """
    Map the coordinate from the image with src shape into the coordinate with
    the dst shape
    src_shape:      [height, width, ...]
    dst_shape:      [height, width, ...]
    coord:          [height, width]
    """
    h_rate = float(coord[0]) / float(src_shape[0])
    w_rate = float(coord[1]) / float(src_shape[1])
    h = int(float(dst_shape[0]) * h_rate)
    w = int(float(dst_shape[1]) * w_rate)
    h = min(dst_shape[0], h)
    w = min(dst_shape[1], w)
    return [h, w]


def _get_point_list(im_shape, coord, kernel, mask=None):
    """
    Return the non-repeated point list within the image
    If the mask is set, only the true pixel should be selected
    """
    point_list = []
    for point in kernel:
        p = [point[0] + coord[0], point[1] + coord[1]]
        if p[0] >= im_shape[0] or p[0] < 0 or p[1] >= im_shape[1] or p[1] < 0:
            continue
        if mask is not None and not mask[p[0], p[1]]:
            continue
        point_list.append(p)

    return point_list


def _gen_kernel(radius):
    """
    Generate the round kernel according to the radius
    the return is a point list corresponding to the kernel
    """
    point_list = []
    for h in range(radius+1):
        max_w = int(np.sqrt(radius*radius - h*h))
        for w in range(max_w+1):
            point1 = [h, w]
            point2 = [h, -w]
            point3 = [-h, w]
            point4 = [-h, -w]
            if point1 not in point_list:
                point_list.append(point1)
            if point2 not in point_list:
                point_list.append(point2)
            if point3 not in point_list:
                point_list.append(point3)
            if point4 not in point_list:
                point_list.append(point4)
    return point_list


def _calc_gradient(dep, point_list, coord, focal):
    """
    Calc the x and y gradient
    """
    central_dep = dep[coord[0], coord[1]]
    x_grad_list = []
    y_grad_list = []
    # Iter the point list
    for point in point_list:
        dep_val = dep[point[0], point[1]]
        dep_diff = dep_val - central_dep
        x_dist = (point[1] - coord[1]) / focal
        y_dist = (point[0] - coord[0]) / focal
        if x_dist != 0:
            x_grad = float(dep_diff) / float(x_dist)
            x_grad_list.append(x_grad)
        if y_dist != 0:
            y_grad = float(dep_diff) / float(y_dist)
            y_grad_list.append(y_grad)

    x_grad = np.array(x_grad_list).mean()
    y_grad = np.array(y_grad_list).mean()
    return x_grad, y_grad


def _normalize(x, y, z):
    """
    Normalize the surface normal
    """
    length = np.sqrt(x*x + y*y + z*z)
    return float(x) / length, float(y) / length, float(z) / length
