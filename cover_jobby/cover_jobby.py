import requests
import argparse
import csv
import shutil
import logging

from math import floor
from pathlib import Path

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

def put_images_into_array(image_list, output_path, array_width, array_height, buffer):
    row_count = 0
    column_count = 0
    page_count = 0

    max_columns = array_width - 1
    max_rows = array_height - 1


    array_image = Image.new("RGB", (450 * array_width, 300 * array_height), (255, 255, 255))

    for image_path in image_list:
        
        #if column_count == 0 and row_count == 0:
        #    array_image = Image.new("RGB", (450 * array_width, 300), (255, 255, 255))

        image = Image.open(image_path)

        original_image = array_image    

        if column_count > max_columns and row_count == max_rows:
            output_file = "{}{}.jpg".format(str(output_path), str(page_count))
            array_image.save(output_file, dpi=(300,300))
            column_count = 0
            row_count = 0
            page_count = page_count + 1
            array_image = Image.new("RGB", (450 * array_width, 300 * array_height), (255, 255, 255))
            original_image = array_image
        elif column_count > max_columns:
            row_count = row_count + 1
            column_count = 0



        array_image.paste(original_image, (0, 0))


        x_offset = 0 if column_count == 0 else buffer
        y_offset = 0 if row_count == 0 else buffer

        image_location = (column_count * (image.width + x_offset), row_count * (image.height + y_offset))

        array_image.paste(image, image_location)

        logging.debug("Pasting image at {}, {}, {}".format(image_location, column_count, row_count))

        column_count = column_count + 1

    output_file = "{}{}.jpg".format(str(output_path), str(page_count))
    array_image.save(output_file, dpi=(300,300))

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
    front_cover_path, back_cover_path, full_cover_path, spine_width_in, spine_color
):
    front_cover = Image.open(front_cover_path)
    back_cover = Image.open(back_cover_path)

    dpi = front_cover.info.get('dpi', (None, None))

    spine_width = floor(spine_width_in * dpi[0])

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
    logging.debug("Images merged and saved successfully.")

def create_image_with_single_color(size, color, output_path):
    image = Image.new("RGB", size, color)
    image.save(output_path)
    logging.debug("Image created successfully.")

def rotate_image(image_path, output_path):
    new_image = Image.open(image_path).rotate(180, resample=Image.BICUBIC, expand=True)
    new_image.save(output_path)
    logging.debug("Image rotated successfully")

def get_most_common_color_and_size(image_path):
    image = Image.open(image_path)
    image = image.convert("RGB")
    size = image.size
    pixels = list(image.getdata())
    color_counts = Counter(pixels)
    most_common_color = color_counts.most_common(1)[0][0]
    count = color_counts.most_common(1)[0][1]
    return size, most_common_color, count

def resize_jpeg_real_world(input_path, output_path, target_width_inches, target_height_inches):
    original_image = Image.open(input_path)

    current_dpi = original_image.info.get('dpi', (None, None))

    logging.debug("current dpi --- {}".format(current_dpi))


    # Calculate the target size in pixels
    target_width_pixels = int(target_width_inches * current_dpi[0])
    target_height_pixels = int(target_height_inches * current_dpi[1])

    # Resize the image
    resized_image = original_image.resize((target_width_pixels, target_height_pixels))

    # Save the resized image
    resized_image.save(output_path, dpi=current_dpi)
    logging.debug("Image resized and saved successfully.")

def normalize_dpi(image_path, output_path, target_dpi=300):
    # Open the image
    original_image = Image.open(image_path)

    # Get the current DPI
    current_dpi = original_image.info.get('dpi', (None, None))
    logging.debug("current dpi --- {}".format(current_dpi))

    # Calculate the scale factor for resizing based on target DPI
    if current_dpi[0] is not None and current_dpi[1] is not None:
        scale_factor = target_dpi / current_dpi[0]
    else:
        # If DPI information is not available, set a default scale factor
        scale_factor = 1.0

    # Calculate the new size in pixels
    new_width = int(original_image.width * scale_factor)
    new_height = int(original_image.height * scale_factor)

    # Resize the image
    resized_image = original_image.resize((new_width, new_height))

    # Set the new DPI
    #resized_image.info['dpi'] = (target_dpi, target_dpi)

    # Save the resized image
    resized_image.save(output_path, dpi = (target_dpi, target_dpi))

def download_picture(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        logging.debug("Picture downloaded successfully.")
    else:
        logging.error("Failed to download picture:", response.status_code)

def search_book_api(title, author_fname, author_lname, id):
    
    url = "https://www.googleapis.com/books/v1/volumes"

    param_string = ""
    params = ""

    if id is not None:
        logging.debug("Searching Google Books API for ID = {}".format(id))

        url = url + "/{}".format(id)
        #param_string = "id:{}".format(id)
  
        
    else:
        logging.debug(
            "Searching Google Books API for {} by {} {}".format(
                title, author_fname, author_lname
            )
        )

        author_lname = author_lname.strip().lower()
        author_fname = author_fname.strip().lower()
        title = title.strip().lower()

        if author_lname != "" and author_lname is not None:
            param_string = "intitle:{}+inauthor:{}".format(title, author_lname)
        else:
            param_string = "intitle:{}".format(title)

        params = {"q": param_string}

    try:
        response_json = requests.get(url, params=params).json()
    except Exception as e:
        logging.error("Failed getting response from Google API - {}".format(e)) 
        return None
    #logging.debug(response_json)
    return response_json

def read_book_list(input_file):
    books = []
    with open(input_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            books.append(dict(row))
    return books


def main(args):

    print("* Reading Book List")

    book_list = read_book_list(args.book_list)

    logging.debug("book list - {}".format(book_list))

    print("* Looking up books")

    image_list = []

    for book in book_list:
        title = book["title"].lower()
        author_first_name = book["first_name"].lower()
        author_last_name = book["last_name"].lower()
        override = book["override"]

        print("** Searching for {}, by {} {}".format(title, author_first_name, author_last_name))
        find_book = search_book_api(title, author_first_name, author_last_name, override)

        if find_book != None and override is not None:
            num_results = 1
        elif find_book != None:
            num_results = find_book["totalItems"]
        else:
            num_results = None

        if num_results == 0 or num_results == None:
            logging.error("BOOK NOT FOUND -- {} by {} {}".format(title, author_first_name, author_last_name))
        else:
            volumes = [find_book] if override is not None else find_book["items"]

            first_result = volumes[0]

            logging.debug("--found {}".format(num_results))


            fr_id = first_result["id"]
            fr_vol_info = first_result["volumeInfo"]

            fr_title = fr_vol_info["title"]
            fr_authors = fr_vol_info["authors"]

            fr_canonical_link = fr_vol_info["canonicalVolumeLink"]

            logging.debug("--found canonical link {}".format(fr_canonical_link))

            fr_image_links = fr_vol_info["imageLinks"]
            fr_image_thumbnail = str.replace(fr_image_links["thumbnail"], "&edge=curl", "")

            logging.debug("---top result - {} by {}".format(fr_title, fr_authors))

            logging.debug("----image_link: {}".format(fr_image_thumbnail))


            slugified_title = slugify(fr_title)

            artifact_path = Path('.','cover_jobby','artifacts')

            cover_target = artifact_path / "{}-cover.jpg".format(slugified_title)
            normalized_target = artifact_path / "{}-cover-normalized.jpg".format(slugified_title)
            resize_target = artifact_path / "{}-cover-resized.jpg".format(slugified_title)
            back_cover_target = artifact_path / "{}-cover-back.jpg".format(slugified_title)
            full_cover_target = artifact_path / "{}-cover-full.jpg".format(slugified_title)
            
            if args.flip_cover:
                array_target = artifact_path / "array-flipped-full-page-"
            else:
                array_target = artifact_path / "array-full-page-"

            download_picture(fr_image_thumbnail, cover_target)

            normalize_dpi(cover_target, normalized_target, 300)

            # 5/8" x 13/16"
            #resize_jpeg_real_world(normalized_target, resize_target, 0.625, 0.8125)
            resize_jpeg_real_world(normalized_target, resize_target, 0.650, 0.8350)

            size, most_common_color, count = get_most_common_color_and_size(resize_target)

            avg_red, avg_green, avg_blue = get_average_rgb(cover_target)

            logging.debug(
                "----Average Color is {} with {} occurrences".format(
                    (avg_red, avg_green, avg_blue), count
                )
            )

            if args.flip_cover:
                rotate_image(resize_target, back_cover_target)
            else:
                create_image_with_single_color(size, (avg_red, avg_green, avg_blue), back_cover_target)

            join_covers_with_spine(resize_target, back_cover_target, full_cover_target, 0.125, (avg_red, avg_green, avg_blue))

            image_list.append(full_cover_target)

    #stack_images(image_list, "./cover_jobby/artifacts/all_covers_stacked.jpg")

    print("* Assembling output images")

    put_images_into_array(image_list, array_target, 5, 11, 5)

    if(args.zip_file is not None):
        print("* Zipping Files")
        zip_images(args.zip_file)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cover Jobby")
    parser.add_argument("--book-list", type=str, help="path to the book list")
    parser.add_argument("--zip-file", type=str, help="path for optional zip file")
    parser.add_argument("--debug", action='store_true', help="turn on debug logging")
    parser.add_argument("--clean", action='store_true', help="clean intermediate files after running")
    parser.add_argument("--flip-cover", action='store_true', help="flip the front cover for the back, otherwise average values")

    args = parser.parse_args()

    if(args.debug):
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s', level=logging.ERROR)

    main(args)
