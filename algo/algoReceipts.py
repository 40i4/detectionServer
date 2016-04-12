# 1) find contours of the receipt
# 2) if there are more than 4 vertices, find those which 
# are the most likely to be receipt vertices, mark and show them
# and if there are any missing vertices - assign value [0,0]
import cv2
import numpy as np
import imutils
from transform import four_point_transform
from skimage.filter import threshold_adaptive
import os

font = cv2.FONT_HERSHEY_SIMPLEX


# creates name of transformed image (suffix "_t.jpg")
def create_file_name(file_path):
    print "file_path: " + str(file_path)
    prefix = file_path.split('.')[0]
    file_name = prefix.split('/')[-1]
    path_prefix = prefix.rsplit('/', 1)[0]

    new_file_name = os.path.join(path_prefix, "%s_t.jpg" % file_name)
    print "new file name in function create file name: " + str(new_file_name)
    return new_file_name


def use_image_contour(all_vertices, image):
    height, width, _ = image.shape
    print "height: " + str(height) + " width: " + str(width)
    first_vertex = all_vertices[0]
    second_vertex = all_vertices[1]
    # check if the curve is horizontal or vertical
    if abs(first_vertex[1] - second_vertex[1]) < 0.1 * height:
        print "horizontal curve"

        # if y of the first vertex is on the upper side of image
        if first_vertex[1] < height/2:
            new_vertices = [[first_vertex[0], height], [second_vertex[0], height]]
        # if y of the first vertex is on the bottom side of image
        else:
            new_vertices = [[first_vertex[0], 0], [second_vertex[0], 0]]
    else:
        print "vertical curve"

        # if y of the first vertex is on the left side of image
        if first_vertex[0] < width/2:
            new_vertices = [[width, first_vertex[1]], [width, second_vertex[1]]]
        # if y of the first vertex is on the right side of image
        else:
            new_vertices = [[0, first_vertex[1]], [0, second_vertex[1]]]

    all_vertices = all_vertices + new_vertices

    return all_vertices


# arguments: image to transform, path to
def transform_image(image, path):
    new_file_name = create_file_name(path)
    ratio = image.shape[0] / 500.0
    orig = image.copy()
    image = imutils.resize(image, height=500)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    # find contours; len(cnts) returns no. of contours found
    (cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print "no. of curves found: " + str(len(cnts))

    # if there are no contours found
    if len(cnts) < 1:
        height, width, _ = image.shape
        print "height: " + str(height) + " width: " + str(width)
        # return coordinates of the whole image
        all_vertices = [[0, 0], [width, 0], [width, height], [0, height]]

        print "all vertices: " + str(all_vertices)

        contours = all_vertices
        # draw lines connecting vertices
        # pts = np.array(contours, np.int32)
        # cv2.polylines(image, [pts], True, (0, 255, 255), 2)

        # print vertices' coordinates
        for elem in contours:
            text2 = str(elem[0]) + " " + str(elem[1])
            cv2.putText(image, text2, (elem[0], elem[1]), font, 0.5, (255, 255, 0), 2)

        contours_copy = contours
        contours_copy_np = np.array(contours_copy)
        cv2.drawContours(image, [contours_copy_np], -1, (0, 255, 0), 2)
        warped = four_point_transform(orig, contours_copy_np.reshape(4, 2) * ratio)

        cv2.imwrite("%s" % new_file_name, warped, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        #!return new_file_name, True
        return new_file_name, True, contours

    # if there are some contours found
    else:
        # array of perimeters
        # keeps lengths of perimeters found (no. of perimeters = no. of contours)

        # sort from the longest perimeter to the shortest
        cnts_sorted = sorted(cnts, key=lambda x: cv2.arcLength(x, True), reverse=True)

        peri_arr2 = []
        for elem in cnts_sorted:
            perii = cv2.arcLength(elem, True)
            peri_arr2.append(perii)
        # print "perimeters sorted by length: " + str(peri_arr2)

        # length of the longest perimeter
        peri_max = peri_arr2[0]
        # print "peri max: " + str(peri_max)

        # approxPolyDP returns coordinates of vertices of the longest perimeter
        approx2 = cv2.approxPolyDP(cnts_sorted[0], 0.02 * peri_max, True)
        # print "no of vertices: " + str(len(approx2))

        # find vertices and put them into array all_vertices
        all_vertices = []
        for a in approx2:
            aa = a[0]
            x_coord = aa[0]
            y_coord = aa[1]
            two_vertices = [x_coord, y_coord]
            all_vertices.append(two_vertices)
        # print "all vertices: " + str(all_vertices)

        # if only one curve was found
        if len(all_vertices) == 2:
            # print "peri_arr2: " + str(peri_arr2)
            # print "peri_arr2[0]: " + str(peri_arr2[0])

            # but if there are other curves
            if len(peri_arr2) > 1:
                peri_max2 = peri_arr2[1]
                # print "peri max 2 length: " + str(peri_max2)
                approx3 = cv2.approxPolyDP(cnts_sorted[1], 0.02 * peri_max2, True)
                # print "no of ver: " + str(len(approx3))

                # find another vertical contour
                if len(approx3) == 2:
                    all_vertices2 = []
                    for a in approx3:
                        aa = a[0]
                        x_coord = aa[0]
                        y_coord = aa[1]
                        two_vertices = [x_coord, y_coord]
                        all_vertices2.append(two_vertices)
                    # print "all vertices 2: " + str(all_vertices2)

                    all_vertices = all_vertices + all_vertices2

                # if there is no another vertical contour - use image contour
                else:
                    all_vertices = use_image_contour(all_vertices, image)

            # if there is no other curve found
            else:
                # print 'there is no other curve found'
                all_vertices = use_image_contour(all_vertices, image)

        # find vertices that are most likely to be receipt vertices
        br = ul = bl = ur = []
        max_sum = 0
        min_sum = 10000
        max_sub_x_y = 0
        max_sub_y_x = 0
        for elem in all_vertices:
            sum_x_and_y = elem[0] + elem[1]
            if sum_x_and_y > max_sum:
                max_sum = sum_x_and_y
                br = elem
            if sum_x_and_y < min_sum:
                min_sum = sum_x_and_y
                ul = elem

            if elem[0] - elem[1] > 0:
                if elem[0] - elem[1] > max_sub_x_y:
                    max_sub_x_y = elem[0] - elem[1]
                    ur = elem

            if elem[1] - elem[0] > 0:
                if elem[1] - elem[0] > max_sub_y_x:
                    max_sub_y_x = elem[1] - elem[0]
                    bl = elem

        # print "ul: " + str(ul)
        # print "ur: " + str(ur)
        # print "br: " + str(br)
        # print "bl: " + str(bl)

        contours = []
        contours.append(ul)
        contours.append(ur)
        contours.append(br)
        contours.append(bl)

        # if there are any empty vertices, assign their values to [0,0]
        for elem, val in enumerate(contours):
            if val == []:
                contours[elem] = [0, 0]

        # print "coordinates of vertices ul, ur, br, bl: " + str(contours)

        # print vertices' coordinates
        for elem in contours:
            text2 = str(elem[0]) + " " + str(elem[1])
            cv2.putText(image, text2, (elem[0], elem[1]), font, 0.5, (255, 255, 0), 2)

        contours_copy = contours
        for elem, val in enumerate(contours_copy):
            tab = []
            tab.append(val)
            contours_copy[elem] = tab

        contours_copy_np = np.array(contours_copy)

        cv2.drawContours(image, [contours_copy_np], -1, (0, 255, 0), 2)

        warped = four_point_transform(orig, contours_copy_np.reshape(4, 2) * ratio)

        # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        # warped = threshold_adaptive(warped, 250, offset=20)
        # warped = warped.astype("uint8") * 255
        cv2.imwrite("%s" % new_file_name, warped, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

        #!return new_file_name, True
        return new_file_name, True, contours

    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


def runz(f):
    """
    Processes the image
    :param f: path to file to be processed
    :returns: (str new image absolute path , bool did algorithm succeed)
    """
    try:
        image = cv2.imread(f)
    except:
        #!return '', False
        return '', False, ''

    #!new_img_path, succeeded = transform_image(image, f)
    new_img_path, succeeded, contours = transform_image(image, f)

    #!return new_img_path, succeeded
    return new_img_path, succeeded, contours

#
# def main():
#     #warped, cut_image = transform_image(imageIn)
#     cv2.imshow("cut_image", cut_image)
#     cv2.imshow("warped", imutils.resize(warped, height=500))
#
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
#
#
# if __name__ == "__main__":
#     main()
