import csv
import os.path
import requests
from bs4 import BeautifulSoup as BS

def get_main_part_url(url):
    """Get first part of url common for urls of all districts and towns."""
    return url.rsplit("/", 1)[0]


def get_parties_list(url, municipality):
    """Get list of parties names from any municipality url."""
    parties_list = []
    soup = get_soup(url)
    print("Getting list of parties...")
    for td in get_td_data(soup, "t1sa1 t1sb2", "t2sa1 t2sb2"):
        parties_list.append(td.get_text())
    return parties_list

def get_municipality_data(url, municipality):
    """Get data from any municipality url."""
    url = get_main_part_url(url) + "/" + municipality
    soup = get_soup(url)
    municipality_data = []
    for td in get_td_data(soup,"sa2", "sa3", "sa6", "t1sa2 t1sb3", "t2sa2 t2sb3"):
        municipality_data.append(td.get_text().replace("\xa0", ""))  # append number and delete space from high numbers
    return municipality_data

def get_csv_header(url, municipality_url):
    """Join basic header with names of all parties."""
    header = ["code", "location", "registered", "envelopes", "valid"]
    url = get_main_part_url(url) + "/" + municipality_url
    soup = get_soup(url)
    return header + get_parties_list(url, municipality_url)

def get_soup(url):
    try:
        request = requests.get(url)
        request.raise_for_status()
        return BS(request.text, "html.parser")
    except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema) as err:
        print()
        print("There is problem with parsing url, please check url and internet connection and run again.")
        print("Error description: ")
        print(err)
        exit()

def get_td_data(soup, *args):
    """Get td tags with specific attributes."""
    td_data = soup.find_all("td", headers=args)
    return td_data

def get_municipality_names(soup):
    """Get list of names of municipalities."""
    names = []
    for tab_number in range(1,4):
        for td in (get_td_data(soup, f"t{tab_number}sa1 t{tab_number}sb2")):
            names.append(td.get_text())
    return names

def get_numbers_and_links(soup):
    """Get list of tuples of number and link of all municipalities."""
    nums_and_links = []
    try:
        for tab_number in range(1,4):
            for td in get_td_data(soup, f"t{tab_number}sa1 t{tab_number}sb1"):
                if td.get_text() != "-":
                    nums_and_links.append((td.get_text(), td.a["href"]))
        return nums_and_links
    except TypeError as err:
        print("Cannot get municipalities links, probably due to wrong url at volby.cz")
        print("Error description:", err)
        exit()

def get_municipalities_list(names, nums_and_links):
    """Combine names and links lists to list of lists."""
    print("Getting list of municipalities...")
    try:
        municipalities = [[int(num_and_link[0]), name, num_and_link[1]] for name, num_and_link in zip(names, nums_and_links)]
        print(municipalities)
        return municipalities
    except ValueError as err:
        print("Cannot get municipalities list, probably due to changes of volby.cz website or wrong url on volby.cz")
        print("Error description:", err)
        exit()


def get_table_data(municipality, municipality_data):
    return municipality[:2] + municipality_data


def write_csv(header, table_data, output_file):
    """create csv file, write header and data"""
    with open(output_file, "a+", newline="") as file:
        writer = csv.writer(file)
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            writer.writerow(header)
        writer.writerows(table_data)
    print()
    print(f"File {output_file} was created.")


if __name__ == '__main__':
    print("Sample URL:", "https://volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2111")
    url = input("Please insert the url with list of the municipalities: ")
    filename = input("Insert the name of the file: ")
    filename += ".csv"
    soup = get_soup(url)
    """Get list of lists with number, name and url."""
    municipalities = get_municipalities_list(get_municipality_names(soup), get_numbers_and_links(soup))
    try:
        header = get_csv_header(url, municipalities[0][2])
    except (IndexError, TypeError) as err:
        print()
        print("Cannot get list of municipalities, probably due to wrong url or the volby.cz website has changed.")
        print("Error description:", err)
    else:
        table_data = []
        for municipality in municipalities:  # prepare the list of rows for saving to csv
            print("\r", "Getting data for...", municipality[1], end="")
            municipality_data = get_municipality_data(url, municipality[2])
            table_data.append(get_table_data(municipality, municipality_data))
        write_csv(header, table_data, filename)
