# Cover Jobby

## Description

* Main function reads a list of books in csv format, with header:

  `title, author first name, author last name`
* Overwrite included `example_book_list.csv` sample
* Searches Google books api for title
* If results were found, download the thumbnail of the first result
* Find most frequent color and make back cover + spine
* 'Concatenate' the resulting full image

## Dependencies

`poetry install --with dev`

## Output

Builds images in the `./cover_jobby/artifacts` directory

## Usage

`python cover_jobby/cover_jobby.py --book-list book_list.csv`