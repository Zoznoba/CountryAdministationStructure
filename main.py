import overpass
from overpass.errors import MultipleRequestsError, ServerLoadError, OverpassSyntaxError,UnknownOverpassError
import pickle
import time
import json
import logging


def convert_to_country_code(country, api):
    """Returns letter code of given country"""

    result = api.get(f'''(
  nwr["name:ru"="{country}"]["country_code_iso3166_1_alpha_2"];
  nwr["name:ru"="{country}"]["ISO3166-1"];
);''',responseformat='json')

    if not result['elements']:
        print('No elements by passing this response')
        return None

    code = result['elements'][0]['tags'].get('ISO3166-1', result['elements'][0]['tags'].get('country_code_iso3166_1_alpha_2'))
    return code


def add_regions(raw_data):
    """Add all posible regions from raw_data"""

    global tree
    # add special region for none region cities or towns
    tree.update({'Города без региона': {}})
    for obl in raw_data['features']:
        key = obl['properties'].get('addr:region', obl['properties'].get('is_in:region', None))
        value = {}
        if key:
            tree.update({key: value})
        else:
            continue


def region_relation(city_name, country, api):
    """Connecting to Overpass API and return region which city or town related
        :param city_name: Gets city or town name at language of country where it placed
        :param country: Country
        :param api: Overpass.API()
    """

    query = f'''
            relation["name"="{city_name}"]["population"]["addr:country"="{country}"];'''
    try:
        result = api.get(query)
    except OverpassSyntaxError:
        assert "Query body is currupted"
    except MultipleRequestsError or ServerLoadError:
        return get_administrative(country, api)
    except UnknownOverpassError:
        return None
    else:
        assert "Request undefined error"

    #find region in data
    if result.get('elements'):
        region = result['elements'][0]['tags']['addr:region']
        return region
    else:
        return None


def get_region(raw_node, name, country, api):

    def get_region_by_matches(name):
        global tree
        for reg in tree:
            if name in str(reg):
                return str(reg)
        return None
    
    region = raw_node['properties'].get('addr:region', raw_node['properties'].get('is_in:region', None))
    # Проблемные города с неизвестной областью, ищем с помощью relation и находим коренные города с областями
    if not region:
        region = region_relation(name, country, api)
        if not region:
            region = get_region_by_matches(name)
            if not region:
                print(f'{name} is lost(without region) city ')
                return "Города без региона"

    return region


def get_district(raw_node, name, region):
    #No reason for search district without region, so we just
    if not region:
        return None

    #add here all possible ways to handle disrict
    def get_district_by_matches(name, region):
        global tree
        for district in tree[region]:
            if name in district:
                return district
        return None

    district = raw_node['properties'].get('addr:district', raw_node['properties'].get('is_in:district', None))
    if not district:
        return get_district_by_matches(name, region)

    return district


def add_node_to_tree(raw_node):
    global tree
    population = raw_node['properties'].get('population', 'undefined')
    country = raw_node['properties'].get("addr:country", raw_node['properties'].get('is_in:country', ''))
    prefix = raw_node['properties'].get('name:prefix', 'undefined')
    capital = raw_node['properties'].get('capital', 'undefined')
    admin_level = raw_node['properties'].get('admin_level', 'undefined')
    place = raw_node['properties'].get('place', 'undefined')
    ang_name = raw_node['properties'].get("name:en", 'undefined')
    name = raw_node['properties'].get('name', 'undefined')

    admin_set = get_administrative(name, api)
    # spec-function to handle district
    region = get_region(raw_node, name, country, api)
    #spec-function to handle district
    district = get_district(raw_node, name, region)

    data = {'addr:region': region,
            'name': name,
            'place': place,
            'capital': capital,
            'admin_level': admin_level,
            'is_in:country': country,
            'addr:district ': district,
            'population': population,
            'name:prefix:ru': prefix,
            'ang_name': ang_name,
            'adm_set': admin_set}

    if district and region:  # Есть ли округ у ноды?
        if not district in tree[region]:  # Если в регионе нет такого округа
            tree[region].update({district: [{name: data}, ]})
        else:  # иначе, значит в регионе уже добавлен округ осталось к нему добавить еще одну ноду
            for d in tree[region]:
                if district == d:
                    tree[region][district].append({name: data})
    else:  # Округа нет, значит это просто город или деревня в области
        if not region:
            tree.update({name: data})
        else:
            tree[region].update({name: data})

    return name


def get_places_in_country(country, api):
    '''Connecting to Overpass API and returns cities and towns of chosen country
        :param country: Gets only letter code of country like BY, RU, KZ, US, UK and e.t.c
        :param api: Gets overpass.API object for request
    '''

    query = f'''
            (
            (node["addr:country"="{country}"][ "place"="town"]["official_status"="ru:город"];
            node["addr:country"="{country}"][ "place"="city"];
            node["is_in:country_code"="{country}"][ "place"="city"];
            node["is_in:country_code"="{country}"][ "place"="town"]["official_status"="ru:город"];);
            );
            '''
    if country == 'BY' or country == "KZ":
        query = f'''(node["addr:country"="{country}"][ "place"="town"];
                    node["addr:country"="{country}"][ "place"="city"];
                    node["is_in:country_code"="{country}"][ "place"="city"];
                    node["is_in:country_code"="{country}"][ "place"="town"];);'''

    result = None
    try:
        result = api.get(query)
    except OverpassSyntaxError:
        assert "Query body is currupted"
    except MultipleRequestsError or ServerLoadError:
        return get_places_in_country(country, api)
    else:
        assert "Request undefined error"
    return result


def get_administrative(city_name, api):
    '''Connecting to Overpass API and returns administrative areas of chosen country
            :param city_name: Gets city or town name at language of country where it placed
    '''
    query = f'''
            area["boundary"="administrative"]["addr:city"="{city_name}"];'''
    try:
        result = api.get(query, responseformat='json')
    except MultipleRequestsError or ServerLoadError:
        time.sleep(5)
        return get_administrative(city_name, api)
    except:
        return []
    #put all subareas of town to list
    boundary_list = [adm['tags']['name'] for adm in result['elements']]
    return boundary_list


def build_adm_tree(raw_data):
    global tree
    add_regions(raw_data)
    index = 0
    for raw_node in raw_data['features']:
        while True:
            try:
                name = add_node_to_tree(raw_node)
                break
            except ServerLoadError:
                print('Server sdoh')
        index += 1
        logging.info(f"{index}/{len(raw_data['features'])}-imported {name}")
        print(f"{index}/{len(raw_data['features'])}-imported {name}")


if __name__ == "__main__":
    api = overpass.API()
    country = input('Input country name: ')
    code = convert_to_country_code(country, api)
    if code:
        tree = {}
        raw_data = get_places_in_country(code, api)

        build_adm_tree(raw_data)

        with open(f'data_base_{country}.pickle', 'wb') as f:
            pickle.dump(tree, f)

        with open(f'data_{country}.json', 'w') as f:
            json = json.dump(tree, f)
    else:
        print('Wrong country try another')