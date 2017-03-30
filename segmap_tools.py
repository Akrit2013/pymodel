#!/usr/bin/python

# This tools box contains the functions related to the segment map
# which is as label map normally begin with 0
import numpy as np
import tools
import glog as log
import pdb


def get_neighbor_ids(segmap, label):
    """
    Given the current superpixel label, and return the label list which is
    the neighbor superpixels
    """
    max_h = segmap.shape[0] - 1
    max_w = segmap.shape[1] - 1
    pos_hw = np.where(segmap == label)

    label_h_list = pos_hw[0]
    label_w_list = pos_hw[1]

    up_h_list = label_h_list - 1
    up_h_list[up_h_list < 0] = 0

    down_h_list = label_h_list + 1
    down_h_list[down_h_list > max_h] = max_h

    left_w_list = label_w_list - 1
    left_w_list[left_w_list < 0] = 0

    right_w_list = label_w_list + 1
    right_w_list[right_w_list > max_w] = max_w

    # Check the label
    # 4-connection
    upper = segmap[up_h_list, label_w_list]
    down = segmap[down_h_list, label_w_list]
    left = segmap[label_h_list, left_w_list]
    right = segmap[label_h_list, right_w_list]

    # 8-connection
    upper_left = segmap[up_h_list, left_w_list]
    upper_right = segmap[up_h_list, right_w_list]
    down_left = segmap[down_h_list, left_w_list]
    down_right = segmap[down_h_list, right_w_list]

    combine = upper.tolist() + down.tolist() + left.tolist() + right.tolist()\
        + upper_left.tolist() + upper_right.tolist() + down_left.tolist()\
        + down_right.tolist()
    combine = np.unique(combine)
    combine = combine.tolist()
    combine.remove(label)
    return combine


def check_if_neighbor(segmap, label1, label2):
    """
    Check if two superpixel blocks are nearby each other
    """
    max_h = segmap.shape[0] - 1
    max_w = segmap.shape[1] - 1

    pos_hw = np.where(segmap == label1)
    label1_h_list = pos_hw[0]
    label1_w_list = pos_hw[1]

    up_h_list = label1_h_list - 1
    up_h_list[up_h_list < 0] = 0

    down_h_list = label1_h_list + 1
    down_h_list[down_h_list > max_h] = max_h

    left_w_list = label1_w_list - 1
    left_w_list[left_w_list < 0] = 0

    right_w_list = label1_w_list + 1
    right_w_list[right_w_list > max_w] = max_w

    # Check the label
    # 4-connection
    upper = segmap[up_h_list, label1_w_list]
    down = segmap[down_h_list, label1_w_list]
    left = segmap[label1_h_list, left_w_list]
    right = segmap[label1_h_list, right_w_list]

    # 8-connection
    upper_left = segmap[up_h_list, left_w_list]
    upper_right = segmap[up_h_list, right_w_list]
    down_left = segmap[down_h_list, left_w_list]
    down_right = segmap[down_h_list, right_w_list]

    if label2 in upper or label2 in down or label2 in right or label2 in left:
        return True

    if label2 in upper_left or label2 in upper_right or\
            label2 in down_right or label2 in down_left:
        return True
    return False


def get_central_coord(segmap, label):
    """
    Get the central coordinate of a certain superpixel
    """
    pos_hw = np.where(segmap == label)

    label_h_list = pos_hw[0]
    label_w_list = pos_hw[1]

    return round(label_h_list.mean()), round(label_w_list.mean())


def superpixel_unpool(segmap, vec):
    """
    Unpooling the vec into the segment image
    The size of the vec must equal with the number of the superpixels
    The vec can be a [n] dim vec, or can be a [n, c] image, the c indicate
    the channels
    """
    vec = np.array(vec)
    if vec.ndim == 1:
        return superpixel_unpool_channel(segmap, vec)
    if vec.ndim > 2:
        log.error('\033[01;31mERROR\033[0m: The channel must be \
smaller than 2')
        return
    rst = np.zeros([segmap.shape[0], segmap.shape[1], vec.shape[1]])
    for i in range(vec.shape[1]):
        rst[:, :, i] = superpixel_unpool_channel(segmap, vec[:, i])
    return rst


def superpixel_unpool_channel(segmap, vec):
    """
    Only can unpool a one channel image
    """
    if vec.ndim > 1:
        log.error('\033[01;31mERROR\033[0m: The channels must be 1')
        return

    rst = np.zeros(segmap.shape)
    for i in range(len(vec)):
        rst[segmap == i] = vec[i]
    return rst


def superpixel_unpool_with_normal(segmap, dep_vec, norm_vec, fx, fy,
                                  boundary=0):
    """
    This function is an extend version of the superpixel_unpool
    This function will take the normal vector direction into consideration
    which means it will produce a much smooth depth map than the
    superpixel_unpool function.
    PARAM:
        segmap      The segment map with full resolution
        dep_vec     The depth vector corresponding to each superpixel
        norm_vec    The normal vector corresponding to each superpixel
        fx          The focal length (in pixel) of col
        fy          The focal length (in pixel) of row
    NOTE:
        Different from the superpixel_unpool function, this function
        can only produce the depth map that means the channel of the
        dep_vec must be one
    """
    dep_vec = np.array(dep_vec)
    norm_vec = np.array(norm_vec)
    if dep_vec.ndim > 1:
        log.error('\033[01;31mERROR\033[0m: The channel number of dep \
vec must be 1')
        return

    if norm_vec.ndim != 2:
        log.error('\033[01;31mERROR\033[0m: The channel number of norm \
vec must be 2')
        return

    dep_map = np.zeros(segmap.shape)

    # Iter the superpixel
    for i in range(len(dep_vec)):
        # The normal vector of the superpixel
        norm = norm_vec[i, :]
        # TODO: The Z is reversed
        dx = -norm[0] / abs(norm[2])
        dy = -norm[1] / abs(norm[2])
        # Get the pixel location of the current superpixel
        pos_hw = np.where(segmap == i)

        label_h_list = pos_hw[0]
        label_w_list = pos_hw[1]
        h_central = round(label_h_list.mean())
        w_central = round(label_w_list.mean())

        curr_dep = dep_vec[i]

        # Iter the pixels
        for h, w in zip(label_h_list, label_w_list):
            ph_diff = h - h_central
            pw_diff = w - w_central
            h_diff = ph_diff * curr_dep / fy
            w_diff = pw_diff * curr_dep / fx
            pred_dep = curr_dep + dx * w_diff + dy * h_diff
            if boundary != 0:
                rate = pred_dep / curr_dep
                if rate > 1 + boundary or rate < 1 - boundary:
                    pred_dep = curr_dep
            dep_map[h, w] = pred_dep

    return dep_map


def superpixel_unpool_with_interp(segmap,
                                  dep_vec,
                                  norm_vec,
                                  rad_thd,
                                  dep_map=None):
    """
    This is another version of the superpixel_unpool.
    This version use interpolation to make the depth map smoother.
    It will gather the superpixel into groups according to their normal vector
    and perform the interpolation WITHIN the group.
    NOTE:
        Since their is possibility that some superpixel can not be grouped
        this function support the predefined dep map. If the dep_map param
        is set, it will be considered as the default depth if a superpixel
        is not connected with others
    """
    dep_vec = np.array(dep_vec)
    norm_vec = np.array(norm_vec)
    if dep_vec.ndim > 1:
        log.error('\033[01;31mERROR\033[0m: The channel number of dep \
vec must be 1')
        return

    if norm_vec.ndim != 2:
        log.error('\033[01;31mERROR\033[0m: The channel number of norm \
vec must be 2')
        return

    if dep_map is None:
        dep_map = np.zeros(segmap.shape)
        predefined = False
    else:
        predefined = True

    # Calc the central points of each superpixel
    central_points_list = []
    for i in range(len(dep_vec)):
        h_central, w_central = get_central_coord(segmap, i)
        central_points_list.append([h_central, w_central])

    # Iter the superpixels
    global_neighbor_list = []
    for i in range(len(dep_vec)):
        neighbor_list = get_neighbor_ids(segmap, i)
        # Judge if the neighbor superpixel are in the same plan
        group = []
        for neighbor in neighbor_list:
            if _is_same_plane(norm_vec[i, :], norm_vec[neighbor, :], rad_thd):
                group.append(neighbor)
        global_neighbor_list.append(group)

    # Extend the neighbor list, that means the patches will be not be only
    # connected to the neighbor superpixel, but also the pathes which its
    # neighbor are connected
    for i in range(len(dep_vec)):
        neighbor_list = global_neighbor_list[i]
        ext_neighbor_list = []
        ext_neighbor_list.extend(neighbor_list)
        for neighbor in neighbor_list:
            ext_neighbor_list.extend(global_neighbor_list[neighbor])
        # Add itself
        ext_neighbor_list.append(i)
        ext_neighbor_list = np.unique(ext_neighbor_list)

        dep = dep_vec[i]

        if neighbor_list == []:
            if predefined:
                continue
            dep_map[segmap == i] = dep
            continue

        # Build the corresponding central points list
        local_central_points_list = []
        for neighbor in ext_neighbor_list:
            local_central_points_list.append(central_points_list[neighbor])

        # Iter the all pixels in the current superpixel
        pos_hw = np.where(segmap == i)

        label_h_list = pos_hw[0]
        label_w_list = pos_hw[1]

        for h, w in zip(label_h_list, label_w_list):
            # Search the nearist 'four corner' central points
            points_list, id_list = \
                _get_surrounding_points([h, w], local_central_points_list,
                                        ext_neighbor_list)

            dist_list = []
            dep_list = []
            for center, idd in zip(points_list, id_list):
                dist_list.append(_dist([h, w], center))
                dep_list.append(dep_vec[idd])

            dist_list = np.array(dist_list)
            dist_sum = dist_list.sum()
            weight_list = dist_sum - dist_list
            weight_list = weight_list / weight_list.sum()
            # Perform the interpolation
            interp_val = np.dot(weight_list, dep_list)
            dep_map[h, w] = interp_val
    return dep_map


def _is_same_plane(norm1, norm2, thd):
    """
    Check if the two superpixel are in the same plane
    according to the normal direction
    """
    # Calc the angle between two vector
    if _angle(norm1, norm2) < thd:
        return True
    else:
        return False


def _angle(vec1, vec2):
    """
    Calc the angle between two vectors
    """
    val = np.dot(vec1, vec2)
    c = val / np.linalg.norm(vec1) / np.linalg.norm(vec2)
    angle = np.arccos(min(1, max(-1, c)))
    return angle


def _dist(point1, point2):
    """
    Calc the distance between two points
    """
    return np.linalg.norm(np.array(point1) - np.array(point2))


def _get_surrounding_points(point, points_list, id_list):
    """
    Get the four nearest surrending points from the points_list
    if can not find enough points, the result will be less than
    four poinst
    """
    # Init the return value
    rst_points_list = []
    rst_id_list = []
    # Calc the distance between the points_list and the point
    dist_list = []
    for point_sr in points_list:
        dist_list.append(_dist(point, point_sr))

    points_list = np.array(points_list)
    id_list = np.array(id_list)
    dist_list = np.array(dist_list)

    # Find the top points
    tmp_points_list = points_list[points_list[:, 0] <= point[0], :]
    tmp_id_list = id_list[points_list[:, 0] <= point[0]]
    tmp_dist_list = dist_list[points_list[:, 0] <= point[0]]

    if tmp_points_list.size != 0:
        idx = np.where(tmp_dist_list == tmp_dist_list.min())
        # If have mutiple result, only take the first
        idx = idx[0][0]
        p = tmp_points_list[idx, :]
        idd = tmp_id_list[idx]
        rst_points_list.append(p)
        rst_id_list.append(idd)
        # Exclude the selected idx
        dist_list[idx] = float('inf')

    # Find the bottom points
    tmp_points_list = points_list[points_list[:, 0] > point[0], :]
    tmp_id_list = id_list[points_list[:, 0] > point[0]]
    tmp_dist_list = dist_list[points_list[:, 0] > point[0]]
    if tmp_points_list.size != 0:
        idx = np.where(tmp_dist_list == tmp_dist_list.min())
        # If have mutiple result, only take the first
        idx = idx[0][0]
        p = tmp_points_list[idx, :]
        idd = tmp_id_list[idx]
        rst_points_list.append(p)
        rst_id_list.append(idd)
        # Exclude the selected idx
        dist_list[idx] = float('inf')

    # Find the left points
    tmp_points_list = points_list[points_list[:, 1] <= point[1], :]
    tmp_id_list = id_list[points_list[:, 1] <= point[1]]
    tmp_dist_list = dist_list[points_list[:, 1] <= point[1]]
    if tmp_points_list.size != 0:
        idx = np.where(tmp_dist_list == tmp_dist_list.min())
        # If have mutiple result, only take the first
        idx = idx[0][0]
        p = tmp_points_list[idx, :]
        idd = tmp_id_list[idx]
        rst_points_list.append(p)
        rst_id_list.append(idd)
        # Exclude the selected idx
        dist_list[idx] = float('inf')

    # Find the right points
    tmp_points_list = points_list[points_list[:, 1] > point[1], :]
    tmp_id_list = id_list[points_list[:, 1] > point[1]]
    tmp_dist_list = dist_list[points_list[:, 1] > point[1]]
    if tmp_points_list.size != 0:
        idx = np.where(tmp_dist_list == tmp_dist_list.min())
        # If have mutiple result, only take the first
        idx = idx[0][0]
        p = tmp_points_list[idx, :]
        idd = tmp_id_list[idx]
        rst_points_list.append(p)
        rst_id_list.append(idd)

    return rst_points_list, rst_id_list


def superpixel_unpool_with_interp_ex(segmap,
                                     dep_vec,
                                     norm_vec,
                                     rad_thd,
                                     fx,
                                     fy,
                                     dep_map=None):
    """
    Different from the superpixel_unpool_with_interp, this function take both
    normal and depth into consideration to judge whether the superpixel are
    connected together
    --------------------------------------------------------------------
    This is another version of the superpixel_unpool.
    This version use interpolation to make the depth map smoother.
    It will gather the superpixel into groups according to their normal vector
    and perform the interpolation WITHIN the group.
    NOTE:
        Since their is possibility that some superpixel can not be grouped
        this function support the predefined dep map. If the dep_map param
        is set, it will be considered as the default depth if a superpixel
        is not connected with others
    """
    dep_vec = np.array(dep_vec)
    norm_vec = np.array(norm_vec)
    if dep_vec.ndim > 1:
        log.error('\033[01;31mERROR\033[0m: The channel number of dep \
vec must be 1')
        return

    if norm_vec.ndim != 2:
        log.error('\033[01;31mERROR\033[0m: The channel number of norm \
vec must be 2')
        return

    if dep_map is None:
        dep_map = np.zeros(segmap.shape)
        predefined = False
    else:
        predefined = True

    # Calc the central points of each superpixel
    central_points_list = []
    for i in range(len(dep_vec)):
        h_central, w_central = get_central_coord(segmap, i)
        central_points_list.append([h_central, w_central])

    # Iter the superpixels
    global_neighbor_list = []
    for i in range(len(dep_vec)):
        neighbor_list = get_neighbor_ids(segmap, i)
        # Judge if the neighbor superpixel are in the same plan
        group = []
        for neighbor in neighbor_list:
            if _is_same_plane_ex(norm_vec[i, :], norm_vec[neighbor, :],
                                 dep_vec[i], dep_vec[neighbor],
                                 central_points_list[i],
                                 central_points_list[neighbor],
                                 fx,
                                 fy,
                                 rad_thd,
                                 rad_thd):
                group.append(neighbor)
        global_neighbor_list.append(group)

    # Extend the neighbor list, that means the patches will be not be only
    # connected to the neighbor superpixel, but also the pathes which its
    # neighbor are connected
    for i in range(len(dep_vec)):
        neighbor_list = global_neighbor_list[i]
        ext_neighbor_list = []
        ext_neighbor_list.extend(neighbor_list)
        for neighbor in neighbor_list:
            ext_neighbor_list.extend(global_neighbor_list[neighbor])
        # Add itself
        ext_neighbor_list.append(i)
        ext_neighbor_list = np.unique(ext_neighbor_list)

        dep = dep_vec[i]

        if neighbor_list == []:
            if predefined:
                continue
            dep_map[segmap == i] = dep
            continue

        # Build the corresponding central points list
        local_central_points_list = []
        for neighbor in ext_neighbor_list:
            local_central_points_list.append(central_points_list[neighbor])

        # Iter the all pixels in the current superpixel
        pos_hw = np.where(segmap == i)

        label_h_list = pos_hw[0]
        label_w_list = pos_hw[1]

        for h, w in zip(label_h_list, label_w_list):
            # Search the nearist 'four corner' central points
            points_list, id_list = \
                _get_surrounding_points([h, w], local_central_points_list,
                                        ext_neighbor_list)

            dist_list = []
            dep_list = []
            for center, idd in zip(points_list, id_list):
                dist_list.append(_dist([h, w], center))
                dep_list.append(dep_vec[idd])

            dist_list = np.array(dist_list)
            dist_sum = dist_list.sum()
            weight_list = dist_sum - dist_list
            weight_list = weight_list / weight_list.sum()
            # Perform the interpolation
            interp_val = np.dot(weight_list, dep_list)
            dep_map[h, w] = interp_val
    return dep_map


def _is_same_plane_ex(norm1, norm2, dep1, dep2, center1, center2,
                      fx, fy, thd_norm, thd_plane):
    """
    This function not only check angle of the normal vectors, but also
    Check the relationship between the depth and the normal vector
    -------------------------------------------------
    norm:   The normal vector of the superpixel
    dep:    The depth value of superpixel
    center: The center coordinate of the superpixel
    fx,fy:  The camera focal length
    """
    # Calc the angle between two vector
    if _angle(norm1, norm2) > thd_norm:
        return False

    # Calc the vector between two center points
    dxp = center1[1] - center2[1]
    dyp = center1[0] - center2[0]
    dz = dep1 - dep2
    # Convert the pixel to real length
    dx = (dep1 + dep2) / 2 * dxp / fx
    dy = (dep1 + dep2) / 2 * dyp / fy
    # The vector between the two superpixel
    vec = np.array([dx, dy, dz])
    # Average the normal vector
    norm_avg = norm1 + norm2
    # Calc the angle between the two vector
    ang = _angle(vec, norm_avg)
    if abs(ang - 3.1416 / 2) < thd_plane:
        return True
    else:
        return False


def get_border_pixels(segmap, label):
    """
    Given a segmap and the label, get the border pixels of the superpixel
    """
    pixel_list = np.where(segmap == label)
    h_list = pixel_list[0]
    w_list = pixel_list[1]
    rst_list = []
    height = segmap.shape[0]
    width = segmap.shape[1]
    # Iter all points
    for h, w in zip(h_list, w_list):
        hn = max(0, h-1)
        hp = min(height-1, h+1)
        wn = max(0, w-1)
        wp = min(width-1, w+1)
        if segmap[hn, w] != label or\
                segmap[hp, w] != label or\
                segmap[h, wn] != label or\
                segmap[h, wp] != label or\
                segmap[hn, wn] != label or\
                segmap[hn, wp] != label or\
                segmap[hp, wn] != label or\
                segmap[hp, wp] != label:
            rst_list.append([h, w])
    return rst_list


def bilinear_superpixel_pooling(segmap, predmap, ref_num=None,
                                pred_coord_map=None):
    """
    Different from the standard superpixel pooling approach
    This function perform the bilinear superpixel pooling, which is
    suitable when the resolution of the predmap is considerably small
    comparing with the number of superpixel

    Parameters:

    ref_num:
        The reference pixel number of each superpixel, if not set, it
        equals to pixel number of predmap / superpixel number

    pred_coord_map:
        The predefined prediction coordinate map.
        Since given the size of segmap and the predmap, the pred_coord_map
        is fixed. So when process large mount of same size data, the caller
        function pre-calc this data will save a lot of time
        The shape of the pred_coord_map is [h, w, 2], first channel is H
        and second channel is W
    """
    segmap_len = len(np.unique(segmap))
    segmap_max = segmap.max()
    if segmap_max + 1 != segmap_len:
        log.error('\033[01;31mERROR\033[0m: The label of the segmap might \
not be continuous. %d vs %d' % (segmap_max+1, segmap_len))
    pixel_num = predmap.shape[0] * predmap.shape[1]
    if ref_num is None:
        ref_num = pixel_num / segmap_len

    # Generate the pred_coord_map if needed
    if pred_coord_map is None:
        pred_coord_map = _gen_square_coord_map(segmap.shape[0],
                                               segmap.shape[1],
                                               predmap.shape[0],
                                               predmap.shape[1])
    # Generate the central coord list for segmap
    seg_coord_list = []
    for label in range(segmap_len):
        h_central, w_central = get_central_coord(segmap, label)
        seg_coord_list.append([h_central, w_central])

    if predmap.ndim == 2:
        rst = np.zeros(segmap_len)
    elif predmap.ndim == 3:
        rst = np.zeros([segmap_len, predmap.shape[2]])
    else:
        log.error('\033[01;31mERROR\033[0m: Only support the predmap with 2 or 3 \
dimension. %d' % predmap.ndim)
        return None

    # The projection rate between the segmap and the predmap
    h_rate = float(segmap.shape[0]) / float(predmap.shape[0])
    w_rate = float(segmap.shape[1]) / float(predmap.shape[1])

    # Iter the labels
    for label in range(segmap_len):
        # Get the H and W range of the current superpixel
        pos_hw = np.where(segmap == label)
        h_list = pos_hw[0]
        w_list = pos_hw[1]
        h_min = h_list.min()
        h_max = h_list.max()
        w_min = w_list.min()
        w_max = w_list.max()
        # Project the range to the predmap
        hp_min = int(float(h_min) / h_rate)
        hp_max = int(float(h_max) / h_rate + 1.0)
        wp_min = int(float(w_min) / w_rate)
        wp_max = int(float(w_max) / w_rate + 1.0)
        # Get the central points list of the predmap
        # Calc the dist between the central point to the ref points
        pred_val_list = []
        dist_list = []
        for hp in range(hp_min, hp_max):
            for wp in range(wp_min, wp_max):
                dist_list.append(_dist(seg_coord_list[label],
                                       pred_coord_map[hp, wp, :]))
                pred_val_list.append(predmap[hp, wp])

        # Sort according to the dist
        # TODO: When two dist are exact the same, there might be
        # a problem
        dist_dict = dict(zip(dist_list, pred_val_list))
        pred_val_list = tools.sorted_dict_values(dist_dict)
        dist_list.sort()

        # bilinear interpolate
        ref_size = min(ref_num, len(dist_list))
        dist_total = np.sum(dist_list[0: ref_size])
        weight_list = []
        for dist in dist_list[0: ref_size]:
            # Small dist get bigger weigth
            weight_list.append(dist_total - dist)
        weight_arr = np.array(weight_list)
        if weight_arr.sum() == 0:
            weight_arr = [1]
        else:
            weight_arr = weight_arr / weight_arr.sum()
        # Interpolation
        val = np.zeros(pred_val_list[0].shape)
        for weight, pred_val in zip(weight_arr, pred_val_list):
            val += weight * pred_val

        rst[label] = val

    return rst


def _gen_square_coord_map(hi_height, hi_width, lo_height, lo_width):
    rst = np.zeros([lo_height, lo_width, 2])
    h_rate = float(hi_height) / float(lo_height)
    w_rate = float(hi_width) / float(lo_width)

    for h in range(lo_height):
        for w in range(lo_width):
            rst[h, w, 0] = h * h_rate + h_rate / 2.0
            rst[h, w, 1] = w * w_rate + w_rate / 2.0
    return rst
