from bs4 import BeautifulSoup
import requests

BASE_URL = 'https://vstup.osvita.ua'

DEGREES = {'Бакалавр': ' (на основі Повна загальна середня освіта)',
            'Магiстр': ' (на основі Бакалавр)'}


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


def get_region_codes(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    select_tag = soup.find('select')
    options = select_tag.find_all('option')
    regions_codes = {option.text: option['value'] for option in options}
    return regions_codes


def has_speciality(div, specialities):
    speciality_name = div.find('a').text
    speciality_code = speciality_name[:3]
    return speciality_code in specialities


def get_tag_value(div, key):
    tag = div.find(text=key)
    if tag:
        return tag.parent.next.next


def get_speciality_name(div):
    speciality_tag = div.find('a')
    if speciality_tag:
        return speciality_tag.text


def get_points(div):
    points = div.find_all(class_='stat_old')
    result = {}
    if points:
        for point in points:
            if 'контракт' in point.text:
                result['contract_points'] = point.text[-6:]
            if 'бюджет' in point.text:
                result['budget_points'] = point.text[-6:]
    result.setdefault('contract_points', 'Iнформацiя вiдсутня')
    result.setdefault('budget_points', 'Iнформацiя вiдсутня')
    return result


def get_speciality_info(education_form, degree, speciality_codes):
    degree_results = education_form.find_all(text=DEGREES[degree])
    divs = (div.parent.parent for div in degree_results)
    divs_with_specialities = filter(lambda div: has_speciality(div, speciality_codes), divs)
    specialities = []
    for div in divs_with_specialities:
        speciality_info = dict()
        speciality_info['degree'] = degree
        speciality = get_speciality_name(div)
        speciality_info['name'] = speciality if speciality else 'Iнформацiя вiдсутня'
        faculty = get_tag_value(div, 'Факультет:')
        speciality_info['faculty'] = faculty if faculty else 'Iнформацiя вiдсутня'
        offer = get_tag_value(div, 'Тип пропозиції:')
        speciality_info['offer'] = offer if offer else 'Iнформацiя вiдсутня'
        contract = get_tag_value(div, 'Обсяг на контракт:')
        speciality_info['contract_places'] = contract if contract else 'Iнформацiя вiдсутня'
        budget = get_tag_value(div, 'Максимальний обсяг держ замовлення')
        speciality_info['budget_places'] = budget[1:] if budget else 'Iнформацiя вiдсутня'
        points = get_points(div)
        speciality_info.update(points)
        specialities.append(speciality_info)
    return specialities


async def parse_specialities(session, url, speciality_codes):
    page = await fetch(session, url)
    soup = BeautifulSoup(page, 'html.parser')

    full_time = soup.find(class_='panel den')
    part_time = soup.find(class_='panel zaoch')

    if full_time:
        bachelor_specialities = get_speciality_info(education_form=full_time,
                                                    degree='Бакалавр',
                                                    speciality_codes=speciality_codes)
        master_specialities = get_speciality_info(education_form=full_time,
                                                  degree='Магiстр',
                                                  speciality_codes=speciality_codes)
        full_time_specs = bachelor_specialities + master_specialities
    else:
        full_time_specs = None

    if part_time:
        bachelor_specialities = get_speciality_info(education_form=part_time,
                                                    degree='Бакалавр',
                                                    speciality_codes=speciality_codes)
        master_specialities = get_speciality_info(education_form=part_time,
                                                  degree='Магiстр',
                                                  speciality_codes=speciality_codes)
        part_time_specs = bachelor_specialities + master_specialities
    else:
        part_time_specs = None

    return {'full_time': full_time_specs, 'part_time': part_time_specs}


async def add_specs_to_univer(session, url, univer, specialities):
    specialities = await parse_specialities(session, url, specialities)
    if specialities:
        univer['specialities'] = specialities
        return univer
