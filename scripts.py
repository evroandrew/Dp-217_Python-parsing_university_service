import requests
from data import REGIONS, SPECIALITIES
import asyncio
from aiohttp import ClientSession
import time
from bs_parser import get_region_codes, add_specs_to_univer, BASE_URL

EDUCATION_TYPES = {'Університет', 'Академія', 'Інститут'}


def get_speciality_codes(field, speciality):
    '''Returns the list of speciality codes. If speciality and field are empty returns all codes'''
    if speciality:
        return [speciality]
    if field and not speciality:
        return SPECIALITIES[field]
    return [code for code_list in SPECIALITIES.values() for code in code_list]


def get_universities_by_region(region_code, city):
    '''Returns list of universities IDs in provided region/city'''
    response = requests.get(f'https://registry.edbo.gov.ua/api/universities/?ut=1&lc={region_code}&exp=json')
    universities = response.json()
    if city:
        return [uni['university_id'] for uni in universities if uni['koatuu_name'] == city and
                uni['education_type_name'] in EDUCATION_TYPES]
    return [uni['university_id'] for uni in universities if uni['education_type_name'] in EDUCATION_TYPES]


async def get_university_data(univer_id, session) -> dict:
    print('before request')
    async with session.request('get', f'https://registry.edbo.gov.ua/api/university/?id={univer_id}&exp=json') as response:
        if response.status == 200:
            print('after request')
            data = await response.json()
            return get_univer_info(data)


def has_speciality(univer, speciality_code):
    specialities_id = [speciality['speciality_code'] for speciality in univer['educators']]
    return speciality_code in specialities_id


def get_univer_info(univer):
    '''Returns dictionary with info of the university which has provided speciality'''
    return {'id': univer['university_id'],
            'name': univer['university_name'],
            'financing_type': univer['university_financing_type_name'],
            'address': univer['university_address'],
            'index': univer['post_index_u'],
            'region': univer['region_name'],
            'city': univer['koatuu_name'],
            'phone': univer['university_phone'],
            'mail': univer['university_email'],
            'site': univer['university_site'],
            'specialities': [speciality['speciality_code'] for speciality in univer['educators']]}


async def parse_universities(region: str = None, city: str = None, field: int = None, speciality: str = None):
    # Contains region code or returns all region codes if param is empty
    region_codes = [REGIONS.get(region) if region else [region_code for region_code in REGIONS.values()]]

    # Contains all university IDs. Those IDs depends on region code and city
    univers_ids = [univer_id for code in region_codes for univer_id in get_universities_by_region(code, city)]

    # contains university data
    async with ClientSession() as session:
        univers_data = await asyncio.gather(
            *(get_university_data(uni_id, session) for uni_id in univers_ids)
        )
    speciality_codes = get_speciality_codes(field, speciality)

    univers = []
    for univer in univers_data:
        for speciality in speciality_codes:
            if speciality in univer['specialities']:
                univers.append(univer)
                break
    region_codes = get_region_codes(BASE_URL)
    t = time.time()
    async with ClientSession() as session:
        tasks = []
        for univer in univers:
            url = BASE_URL + region_codes.get(univer['region']) + univer['id']
            tasks.append(asyncio.create_task(
                add_specs_to_univer(session, url, univer, speciality_codes)
            ))
        results = await asyncio.gather(*tasks)

        response = [result for result in results if result]

    print(time.time() - t)
    return response
