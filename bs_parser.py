from bs4 import BeautifulSoup
import requests

BASE_URL = 'https://vstup.osvita.ua'


async def fetch(session, url):
    async with session.get(url) as response:
        print('inside await in fetch')
        return await response.text()


def get_region_codes(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    select_tag = soup.find('select')
    options = select_tag.find_all('option')

    regions_codes = {option.text: option['value'] for option in options}

    return regions_codes


def is_speciality_box(tag):
    return tag.get('class') == ['table-of-specs-item']


def is_open_offer(tag):
    content = tag.text
    if len(content) > 30:
        offer = content.split('\n')[5].split(' ')[2]
        return offer == 'Відкрита'


def get_speciality_name(value):
    speciality = value.split('\xa0i')[0]
    if 'Факультет' in speciality:
        speciality = speciality[0: -9]
    return speciality.strip()


def get_faculty_name(value):
    faculty = value.split('Освітня')[0]
    return faculty.strip()


def get_total_places(element):
    places = element.split('Обсяг:')
    total_places = places[0][-2:]
    return total_places.strip()


def locate_speciality(row):
    return row[4].split(':')


async def parse_specialities(session, url, speciality_codes):
    page = await fetch(session, url)
    soup = BeautifulSoup(page, 'html.parser')
    divs = soup.find_all('div')
    specialities = []
    spec_boxes = filter(is_speciality_box, divs)
    baks = filter(is_open_offer, spec_boxes)
    splitted = (bak.text.split('\n') for bak in baks)
    filtered_splitted = filter(lambda part: get_speciality_name(locate_speciality(part)[1])[:3] in speciality_codes, splitted)

    for row in filtered_splitted:
        speciality = get_speciality_name(locate_speciality(row)[1])
        faculty = get_faculty_name(locate_speciality(row)[2])

        speciality_info = {
            'speciality': speciality,
            'faculty': faculty,
            'total_places': 0,
            'contract_places': 0,
            'free_places': 0,
            'contract_points': 'iнформацiя вiдсутня',
            'free_points': 'iнформацiя вiдсутня'}

        for element in row:
            if 'Ліцензійний обсяг' in element:
                speciality_info['total_places'] = get_total_places(element)
            if 'Максимальний обсяг' in element:
                free_places = element[-2:]
                contract_places = int(speciality_info['total_places']) - int(free_places)
                speciality_info['free_places'] = free_places.strip()
                speciality_info['contract_places'] = str(contract_places)
            if 'Середній балЗНО' in element:
                points = element.split('Середній балЗНО')
                for point in points:
                    if 'контракт' in point:
                        contract_points = point[-7:]
                        speciality_info['contract_points'] = contract_points.strip()
                    if 'бюджет' in point:
                        free_points = point[-7:]
                        speciality_info['free_points'] = free_points.strip()
        specialities.append(speciality_info)
    return specialities


async def add_specs_to_univer(session, url, univer, specialities):
    specialities = await parse_specialities(session, url, specialities)
    if specialities:
        univer['specialities'] = specialities
        print(f'parse_specialities response {specialities}')
        return univer
