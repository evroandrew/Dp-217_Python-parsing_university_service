from json import JSONDecodeError
import requests
from data import REGIONS, SPECIALITIES

# That's the template of url / Шаблон url
# URL_FORMAT = 'univerdata/?region=Миколаївська+область&city=Миколаїв&field=11+Математика+та+статистика&speciality='
# If some param values are empty (speciality=) - we should process all key data
# Если по ключу какое-то значение отстутствует (speciality=), подразумеваем,
# что нужно обработать все значения по данному ключу

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
            'specialities': get_speciality_info(univer, speciality)}


def main(region: str = None, city: str = None, field: int = None, speciality: str = None) -> list:
    # возвращает код региона, если нет - код всех регионов
    # Contains region code or returns all region codes if param is empty
    region_codes = [REGIONS.get(region) if region else [region_code for region_code in REGIONS.values()]]

    # возвразает ид всех универов, ссылаясь на код региона и город
    # Contains all university IDs. Those IDs depends on region code and city
    univers_ids = [univer_id for code in region_codes for univer_id in get_universities_by_region(code, city)]

    # Возвращает данные универов по их ид (univers_ids)
    # contains university data
    univers_data = []
    for item in univers_ids:
        try:
            univers_data.append(get_university_data(item))
        except JSONDecodeError:
            continue

    # Возвращает специальность, если есть специальность
    # Возвращает список специальностей, если есть категория (field) и нет специальности
    # Возвращает коды всех специальностей если не указано ничего
    speciality_codes = get_speciality_codes(field, speciality)

    response = []
    for speciality in speciality_codes:
        univers_with_speciality = filter(lambda univer: has_speciality(univer, speciality), univers_data)
        data = [get_univer_info_by_speciality(univer, speciality) for univer in univers_with_speciality]
        response.extend(data)

    return response


if __name__ == '__main__':
    # Parser check
    print(main('Одеська область', 'Одеса', 9))
