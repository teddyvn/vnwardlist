# Date: 25/07/19
# Package: wikitextparser, mwclient, requests
# Other packages: wikipedia-api
#####################################################
import mwclient
import wikitextparser as wtp
import re
import requests
from urllib.parse import quote
import locale

locale.setlocale(locale.LC_COLLATE, 'vi_VN.UTF-8')
site = mwclient.Site('vi.wikipedia.org')


def get_provinces():
    province_list = []
    page = site.pages["Bản mẫu:Đơn vị hành chính cấp tỉnh Việt Nam"]
    wikitext = page.text()
    parsed = wtp.parse(wikitext)
    for template in parsed.templates:
        for argument in template.arguments:
            if re.fullmatch(r'^list.*\d+$', argument.name):
                parsed_value = wtp.parse(argument.value)
                value_list = parsed_value.get_lists()[0]
                for item in value_list.items:
                    wl = wtp.parse(item).wikilinks[0]
                    province_list.append(wl.title)
    return province_list


def get_template_links():
    link_list = []
    category_name = "Thể loại:Bản mẫu hành chính Việt Nam theo tỉnh thành"
    encoded_name = quote(category_name.replace(' ', '_'))
    api_url = "https://vi.wikipedia.org/w/api.php"
    url = f"{api_url}?action=query&titles={encoded_name}&format=json"
    response = requests.get(url).json()
    page_id = list(response['query']['pages'].keys())[0]
    params = {
        'action': 'query',
        'list': 'categorymembers',
        'cmpageid': str(page_id),
        'cmlimit': 'max',
        'format': 'json'
    }
    response = requests.get(api_url,
                            params=params,
                            headers={'User-Agent': 'vnlist/1.0'}).json()
    for page in response['query']['categorymembers']:
        link_list.append(page['title'])
    return link_list


def extract_innermost_list_values(wikitext):
    parsed = wtp.parse(wikitext)

    # Check recursively and get list if it is the leaf
    def _scan(node):
        list_values = []
        has_nested_list = False

        if hasattr(node, 'templates'):
            for node_template in node.templates:
                for arg in node_template.arguments:

                    child_values, child_has_list = _scan(wtp.parse(arg.value))

                    if re.fullmatch(r'^list\d+$', arg.name.strip()):
                        if not child_has_list:
                            list_values.append(arg.value.strip())
                        has_nested_list = True
                    else:
                        if child_has_list:
                            has_nested_list = True

                    list_values.extend(child_values)

        return list_values, has_nested_list

    values, _ = _scan(parsed)
    return values


def get_ward_list(name):
    ward_list = []
    page = site.pages[name]
    wikitext = page.text()
    list_list = extract_innermost_list_values(wikitext)
    for list_text in list_list:
        parsed_value = wtp.parse(list_text)
        link_list = parsed_value.wikilinks
        for link in link_list:
            ward_name = link.text if link.text is not None else link.title
            ward_list.append(ward_name)
    ward_list.sort(key=locale.strxfrm)
    return ward_list


provinceList = get_provinces()
template_list = get_template_links()
for template in template_list:
    for province in provinceList:
        if province in template:
            provinceList.remove(province)
            break
for template in template_list:
    get_ward_list(template)
for province in provinceList:
    template = r"Bản mẫu:{province}"
    get_ward_list(template)

