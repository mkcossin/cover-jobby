import requests
import argparse
import csv
import json

from slugify import slugify
from PIL import Image
from collections import Counter


def merge_images(image1_path, image2_path, output_path):
    image1 = Image.open(image1_path)
    image2 = Image.open(image2_path)

    merged_width = image1.width + image2.width
    merged_height = image1.height

    merged_image = Image.new("RGB", (merged_width, merged_height), (0, 0, 0))
    merged_image.paste(image1, (0, 0))

    offset_x = image1.width
    merged_image.paste(image2, (offset_x, 0))

    merged_image.save(output_path)
    print("Images merged and saved successfully.")
def create_image_with_single_color(size, color, output_path):
    image = Image.new("RGB", size, color)
    image.save(output_path)
    print("Image created successfully.")

def get_most_common_color_and_size(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    size = image.size
    pixels = list(image.getdata())
    color_counts = Counter(pixels)
    most_common_color = color_counts.most_common(1)[0][0]
    count = color_counts.most_common(1)[0][1]
    return size, most_common_color, count

def resize_jpeg(input_path, output_path, new_width, new_height):
    image = Image.open(input_path)
    resized_image = image.resize((new_width, new_height))
    resized_image.save(output_path)
    print("Image resized and saved successfully.")

def download_picture(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print('Picture downloaded successfully.')
    else:
        print('Failed to download picture:', response.status_code)

def search_book_api(title, author_fname, author_lname):
    print('Searching Google Books API for {} by {} {}'.format(title, author_fname, author_lname))
    url = 'https://www.googleapis.com/books/v1/volumes'

    author_lname = author_lname.strip().lower()
    author_fname = author_fname.strip().lower()
    title = title.strip().lower()

    if(author_lname != '' and author_lname is not None):
        param_string = 'intitle:{}+inauthor:{}'.format(title, author_lname)
    else:
        param_string = 'intitle:{}'.format(title)

    if author_fname is not None or author_lname is not None:
        params = {'q': param_string}
    else:
        params = {'q': param_string }

    response_json = requests.get(url, params=params).json()

    return response_json

def read_book_list(input_file):
    books = []
    with open(input_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            books.append(dict(row))
    return books

def main(args):
    book_list = read_book_list(args.book_list)

    for book in book_list:
        title = book['title'].lower()
        author_first_name = book['first_name'].lower()
        author_last_name = book['last_name'].lower()

        find_book = search_book_api(title, author_first_name, author_last_name)

        num_results = find_book['totalItems']
        volumes = find_book['items']

        first_result = volumes[0]

        print('--found {}'.format(num_results))


        fr_id = first_result["id"]
        fr_vol_info = first_result["volumeInfo"]

        fr_title = fr_vol_info['title']
        fr_authors = fr_vol_info['authors']

        fr_image_links = fr_vol_info['imageLinks']
        fr_image_thumbnail = str.replace(fr_image_links['thumbnail'], '&edge=curl','')

        print('---top result - {} by {}'.format(fr_title, fr_authors))

        print('----image_link: {}'.format(fr_image_thumbnail))

        slugified_title = slugify(fr_title)

        cover_target = "./cover_jobby/artifacts/{}-cover.jpg".format(slugified_title)
        resize_target = "./cover_jobby/artifacts/{}-cover-resized.jpg".format(slugified_title)
        back_cover_target = "./cover_jobby/artifacts/{}-cover-back.jpg".format(slugified_title)
        full_cover_target = "./cover_jobby/artifacts/{}-cover-full.jpg".format(slugified_title)

        download_picture(fr_image_thumbnail, cover_target)

        size, most_common_color, count = get_most_common_color_and_size(cover_target)

        print("----Most Common Color is {} with {} occurrences".format(most_common_color, count))

        create_image_with_single_color((size[0] + 25,size[1]), most_common_color, back_cover_target)

        merge_images(back_cover_target, cover_target, full_cover_target)
        # cover size: .64"W x .87H
        # spine size: .125"W x .87H



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cover Jobby')
    parser.add_argument('--book-list', type=str, help='path to the book list')

    args = parser.parse_args()

    main(args)
