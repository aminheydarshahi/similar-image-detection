import pybktree
from hash_helper import compute_hash
from PIL import Image
import collections
import json
from io import BytesIO
import os
import re

hash_tree = []
Img = None
id_hash_dict = {}


def initialize_bktree():
    global hash_tree, Img, id_hash_dict
    Img = collections.namedtuple('Img', 'hash id')
    id_hash_dict = json.load(open(os.getenv("HASH_LIST", "files/hashlist.txt")))
    hash_tree = pybktree.BKTree(mydistance, [])
    for img_id in id_hash_dict:
        hash_tree.add(Img(int(id_hash_dict[img_id], 16), img_id))


def process_image(file):
    res = Image.open(BytesIO(file.body))
    return res


def find_hash(img):
    hash_string = str(compute_hash(img))
    return hash_string


def find_hash_by_id(id):
    global id_hash_dict
    res = id_hash_dict.get(id)
    return res


def get_hash_from_request(request, request_type):
    global id_hash_dict
    request_by = request.form.get('request_query').strip()  # "hash" or "image" or "id"
    request_id = request.form.get('request_id').strip()
    test_file = request.files.get('theimage')

    error = validate_request(request_by, request_id, request_type, test_file)

    if error != "no_error":
        return "", "", "", error

    if request_by == "hash":
        return request_by, request_id, request.form.get("hash"), error
    elif request_by == "image":
        image = process_image(test_file)
        return request_by, request_id, find_hash(image), error

    elif request_by == "id":
        return request_by, request_id, find_hash_by_id(request_id), error


def add_image(image_hash, id):
    global Img, hash_tree, id_hash_dict

    if id in id_hash_dict:
        return False

    id_hash_dict[id] = image_hash
    hash_tree.add(Img(int(image_hash, 16), id))
    print("image with id " + id + " and hash " + image_hash + " added to hash_tree")
    return True


def find_duplicates(image_hash, distance):
    global Img, hash_tree
    duplicates = []
    duplicate_hashes = hash_tree.find(Img(int(str(image_hash), 16), 0), int(distance))

    for j in range(0, len(duplicate_hashes)):
        duplicates.append(duplicate_hashes[j][1].id)

    return duplicates


def validate_request(request_by, request_id, request_type, test_file):

    valid_files = ['image/jpg', 'image/png']

    # validation

    if request_by not in ["image", "id", "hash"]:
        return "error_request_by"

    if request_type == "add" or request_by == "id":

        if re.fullmatch(r'\s*', request_id):
            return "error_no_id"
        if request_type == "search":
            if find_hash_by_id(request_id) is None:
                return "error_no_id"

    if request_type == "add":
        if request_id in id_hash_dict:
            return "error_existing_id"

    if request_by == "image":
        if test_file is None:
            return "error_no_image"
        if test_file.type not in valid_files:
            return "error_invalid_type"
    return "no_error"


def mydistance(a, b):
    return pybktree.hamming_distance(a.hash, b.hash)


def persist_hash_tree():
    global id_hash_dict
    json.dump(id_hash_dict, open("files/hashlist.txt", 'w'))
