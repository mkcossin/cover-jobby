import requests
import argparse
import csv
import shutil

from slugify import slugify
from PIL import Image
from collections import Counter


def get_average_rgb(image_path):
    # Open the image
    image = Image.open(image_path)

    # Convert the image to RGB mode if it's not already
    image = image.convert('RGB')

    # Get the width and height of the image
    width, height = image.size

    # Initialize variables to store total RGB values
    total_red = 0
    total_green = 0
    total_blue = 0

    # Iterate over each pixel in the image
    for y in range(height):
        for x in range(width):
            # Get the RGB values of the pixel
            red, green, blue = image.getpixel((x, y))

            # Add the RGB values to the totals
            total_red += red
            total_green += green
            total_blue += blue

    # Calculate the average RGB values
    num_pixels = width * height
    avg_red = total_red // num_pixels
    avg_green = total_green // num_pixels
    avg_blue = total_blue // num_pixels

    # Return the average RGB values
    return avg_red, avg_green, avg_blue
def zip_images(output_file_path):
    shutil.make_archive(output_file_path, 'zip', './cover_jobby/artifacts')

def put_images_into_array(image_list, output_path, array_width, array_height):
    row_count = 0
    column_count = 0

    max_columns = array_width

    array_image = Image.new("RGB", (300 * max_columns, 215), (255, 255, 255))

    for image_path in image_list:
        image = Image.open(image_path)

        original_image = array_image


        if column_count >= max_columns:
            row_count = row_count + 1
            column_count = 0
            new_height = original_image.height + 215
        else:
            new_height = original_image.height

        array_image = Image.new(
            "RGB",
            (original_image.width, new_height),
            (255, 255, 255)
        )

        array_image.paste(original_image, (0, 0))

        image_location = (column_count * 300, row_count * 215)

        array_image.paste(image, image_location)

        print("Pasting image at {}, {}, {}".format(image_location, column_count, row_count))

        column_count = column_count + 1

    array_image.save(output_path)


def stack_images(image_list, output_path):
    stacked_image = Image.new("RGB", (300, 0), (0, 0, 0))

    for image_path in image_list:
        image = Image.open(image_path)
        image_height = image.height

        original_image = stacked_image

        stacked_image = Image.new(
            "RGB",
            (original_image.width, original_image.height + image_height),
            (0, 0, 0),
        )

        stacked_image.paste(original_image, (0, 0))

        stacked_image.paste(image, (0, original_image.height))

    stacked_image.save(output_path)


def join_covers_with_spine(
    front_cover_path, back_cover_path, full_cover_path, spine_width, spine_color
):
    front_cover = Image.open(front_cover_path)
    back_cover = Image.open(back_cover_path)

    full_width = front_cover.width * 2 + spine_width

    full_cover = Image.new("RGB", (full_width, front_cover.height), spine_color)

    full_cover.paste(back_cover, (0, 0))
    full_cover.paste(front_cover, (front_cover.width + spine_width, 0))

    full_cover.save(full_cover_path)


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


def rotate_image(image_path, output_path):
    new_image = Image.open(image_path).rotate(180, resample=Image.BICUBIC, expand=True)
    new_image.save(output_path)
    print("Image rotated successfully")


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
        with open(save_path, "wb") as file:
            file.write(response.content)
        print("Picture downloaded successfully.")
    else:
        print("Failed to download picture:", response.status_code)


def search_book_api(title, author_fname, author_lname):
    print(
        "Searching Google Books API for {} by {} {}".format(
            title, author_fname, author_lname
        )
    )
    url = "https://www.googleapis.com/books/v1/volumes"

    author_lname = author_lname.strip().lower()
    author_fname = author_fname.strip().lower()
    title = title.strip().lower()

    if author_lname != "" and author_lname is not None:
        param_string = "intitle:{}+inauthor:{}".format(title, author_lname)
    else:
        param_string = "intitle:{}".format(title)

    params = {"q": param_string}

    response_json = requests.get(url, params=params).json()

    return response_json


def read_book_list(input_file):
    books = []
    with open(input_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            books.append(dict(row))
    return books


def main(args):
    book_list = read_book_list(args.book_list)

    print(book_list)

    image_list = []

    for book in book_list:
        title = book["title"].lower()
        author_first_name = book["first_name"].lower()
        author_last_name = book["last_name"].lower()

        find_book = search_book_api(title, author_first_name, author_last_name)

        num_results = find_book["totalItems"]
        volumes = find_book["items"]

        first_result = volumes[0]

        print("--found {}".format(num_results))

        fr_id = first_result["id"]
        fr_vol_info = first_result["volumeInfo"]

        fr_title = fr_vol_info["title"]
        fr_authors = fr_vol_info["authors"]

        fr_image_links = fr_vol_info["imageLinks"]
        fr_image_thumbnail = str.replace(fr_image_links["thumbnail"], "&edge=curl", "")

        print("---top result - {} by {}".format(fr_title, fr_authors))

        print("----image_link: {}".format(fr_image_thumbnail))

        slugified_title = slugify(fr_title)

        cover_target = "./cover_jobby/artifacts/{}-cover.jpg".format(slugified_title)
        resize_target = "./cover_jobby/artifacts/{}-cover-resized.jpg".format(
            slugified_title
        )
        back_cover_target = "./cover_jobby/artifacts/{}-cover-back.jpg".format(
            slugified_title
        )
        full_cover_target = "./cover_jobby/artifacts/{}-cover-full.jpg".format(
            slugified_title
        )

        download_picture(fr_image_thumbnail, cover_target)

        size, most_common_color, count = get_most_common_color_and_size(cover_target)

        avg_red, avg_green, avg_blue = get_average_rgb(cover_target)

        print(
            "----Average Color is {} with {} occurrences".format(
                (avg_red, avg_green, avg_blue), count
            )
        )

        resize_jpeg(cover_target, resize_target, 128, 200)

        # create_image_with_single_color((size[0] + 25,size[1]), most_common_color, back_cover_target)
        # merge_images(back_cover_target, cover_target, full_cover_target)
        # cover size: .64"W x .87H
        # spine size: .125"W x .87H

        rotate_image(resize_target, back_cover_target)

        join_covers_with_spine(resize_target, back_cover_target, full_cover_target, 30, (avg_red, avg_green, avg_blue))

        image_list.append(full_cover_target)

    stack_images(image_list, "./cover_jobby/artifacts/all_covers_stacked.jpg")

    put_images_into_array(image_list, "./cover_jobby/artifacts/all_covers_array.jpg", 6, 10)

    if(args.zip_file is not None):
        zip_images(args.zip_file)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cover Jobby")
    parser.add_argument("--book-list", type=str, help="path to the book list")
    parser.add_argument("--zip-file", type=str, help="path for optional zip file")

    args = parser.parse_args()

    main(args)
