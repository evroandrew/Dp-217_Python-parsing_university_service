import requests
from data import REGIONS, SPECIALITIES


urlformat = 'univerdata/?region=Миколаївська+область&city=Миколаїв&field=11+Математика+та+статистика&speciality='

# Если по ключу какое-то значение отстутствует (speciality=), подразумеваем,
# что нужно обработать все значения по данному ключу


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
        return [uni['university_id'] for uni in universities if uni['koatuu_name'] == city]
    return [uni['university_id'] for uni in universities]


def get_university_data(univer_id):
    response = requests.get(f'https://registry.edbo.gov.ua/api/university/?id={univer_id}&exp=json')
    return response.json()


def has_speciality(univer, speciality_code):
    specialities_id = [speciality['speciality_code'] for speciality in univer['speciality_licenses']]
    return speciality_code in specialities_id


def get_speciality_info(univer, speciality_code):
    '''Returns list of dictionaries with speciality info'''
    return [{'qualification': speciality['qualification_group_name'],
             'name': speciality['speciality_name'],
             'places': speciality['all_count']} for speciality in univer['speciality_licenses']
            if speciality['speciality_code'] == speciality_code]


def get_univer_info_by_speciality(univer, speciality):
    '''Returns dictionary with info of the university which has provided speciality'''
    return {'name': univer['university_name'],
            'financing_type': univer['university_financing_type_name'],
            'address': univer['university_address'],
            'index': univer['post_index_u'],
            'phone': univer['university_phone'],
            'mail': univer['university_email'],
            'site': univer['university_site'],
            'specialities': get_speciality_info(univer, speciality)}


def main():
# Значения region, city, field, speciality берем из query string (пример url: переменная urlformat)
    region = 'Одеська область'
    city = 'Одеса'
    field = '10'
    speciality = ''

    region_codes = [REGIONS.get(region) if region else [region_code for region_code in REGIONS.values()]]
    univers_ids = [univer_id for code in region_codes for univer_id in get_universities_by_region(code, city)]
    univers_data = [get_university_data(id) for id in univers_ids]
    speciality_codes = get_speciality_codes(field, speciality)
    response = []
    for speciality in speciality_codes:
        univers_with_speciality = filter(lambda univer: has_speciality(univer, speciality), univers_data)
        data = [get_univer_info_by_speciality(univer, speciality) for univer in univers_with_speciality]
        response.extend(data)
    return response


if '__name__' == 'main':
    print(main())
