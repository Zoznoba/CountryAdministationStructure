import pytest
import overpass
import main
import json
api = overpass.API()

# with open('test_responses/test_response_relation_for_Gomel.json', encoding='utf-8') as f:
#     test_response_adm_list_for_Gomel = json.load(f)
#
# with open('test_responses/test_response_relation_for_Lipetsk.json', encoding='utf-8') as f:
#     test_response_adm_list_for_Lipetsk = json.load(f)
#
# with open('test_responses/test_response_relation_for_Astana.json', encoding='utf-8') as f:
#     test_response_relation_for_Astana = json.load(f)
#
# with open('test_responses/test_response_relation_for_wrong.json', encoding='utf-8') as f:
#     test_response_relation_for_wrong = json.load(f)

with open('test_responses/test_response_country_places_BY.json', encoding='utf-8') as f:
    test_response_country_places_BY = json.load(f)


@pytest.mark.parametrize('city_name, adm_list', [('Гомель', ['Железнодорожный район', "Новобелицкий район", "Советский район", "Центральный район"]),
                                                 ('Минск', ["Октябрьский район", "Ленинский район", "Московский район", "Заводской район", "Фрунзенский район", "Советский район"]),
                                                 ('Любой незначительный город', [])])
def test_adm_list(city_name, adm_list):
    api = overpass.API()
    assert main.get_administrative(city_name, api) == adm_list


@pytest.mark.parametrize('city_name, country, response', [('RU', 'Липецк', None),
                                                          ("KZ", 'Астана', None),
                                                          ('BU', 'asbas', None)])
def test_region_relation(city_name, country, response):
    api = overpass.API()
    assert main.region_relation(city_name, country, api) == response


# @pytest.mark.parametrize('country, response', ('BY', test_response_country_places_BY))
# def test_get_places(country, response):
#     api = overpass.API()
#     assert adm_tree.get_places_in_country(country, api) == response


def test_convert_to_country_code():
    api = overpass.API()
    assert main.convert_to_country_code('Россия', api) == 'RU'




