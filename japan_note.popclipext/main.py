import requests
import logging
import json
import os


def word_type_process(type_str):
    """对单词类型字符串进行识别"""
    word_types = []
    if "I-adjective" in type_str:
        word_types.append('イ形')
    if "Noun" in type_str:
        word_types.append('名')
    if "Adverb" in type_str:
        word_types.append('副')
    if "Na-adjective" in type_str:
        word_types.append('ナ形')
    if "verb" in type_str:
        word_types.append(verb_type_process(type_str))
    return ','.join(word_types)


def verb_type_process(type_str):
    """对动词进行识别，返回类型字符串"""
    if "Godan verb" in type_str and ("Transitive verb" in type_str):
        return "他五"
    elif "Godan verb" in type_str and "Intransitive verb" in type_str:
        return "自五"
    elif "Ichidan verb" in type_str and "Transitive verb" in type_str:
        return "他一"
    elif "Ichidan verb" in type_str and "Intransitive verb" in type_str:
        return "自一"
    else:
        return "三类"


class JishoWord:
    """jisho jap word meaning"""
    word = ''
    reading = ''
    meaning_list = []

    def __init__(self, jisho_data):
        status = jisho_data['meta']['status']
        if status != 200:
            raise IOError
        else:
            data_field = jisho_data['data']
            self.word = data_field[0]['japanese'][0]['word']
            self.reading = data_field[0]['japanese'][0]['reading']
            senses = data_field[0]['senses']
            if len(senses) > 3:
                senses = senses[0:3]
            self.meaning_list = list(map(Meaning, senses))

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Meaning:
    """jisho word meaning"""
    type = ''
    definition = ''

    def __init__(self, jisho_sense):
        english_definitions = jisho_sense['english_definitions']
        self.definition = ";".join(english_definitions)
        parts_of_speech = jisho_sense['parts_of_speech']
        speech = ','.join(parts_of_speech)
        types_str = word_type_process(speech)
        self.type = types_str

    def to_json(self):
        return json.dumps(self, default=lambda output: output.__dict__)


logger = logging.getLogger(__name__)


def search_on_jisho(search_word):
    # search word's 意味 on jisho.org
    jisho_url = "https://jisho.org/api/v1/search/words"
    params = {'keyword': search_word}
    response = requests.get(url=jisho_url, params=params)
    response_data = response.json()
    logger.debug("data: ", response_data)
    return response_data


def update_airtable(airtable_url, api_key, jisho_word):
    authorization = 'Bearer ' + api_key
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }
    records = {"records": [{
        "fields": {
            "word": jisho_word.word,
            "spell": jisho_word.reading
        }
    }]}
    index = 1
    for meaning in jisho_word.meaning_list:
        mean = '('+meaning.type+')'+meaning.definition
        key = 'meaning' + str(index)
        records["records"][0]["fields"][key] = mean
        index += 1
    response = requests.post(url=airtable_url, json=records, headers=headers)
    return response.json()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    word = os.environ.get('POPCLIP_FULL_TEXT')
    api_key = os.environ.get('POPCLIP_OPTION_ARITABLE_API_KEY')
    airtable_url = os.environ.get('POPCLIP_OPTION_AIRTABLE_DB_URL')
    data = search_on_jisho(word)
    word = JishoWord(data)
    r = update_airtable(airtable_url, api_key,word)
    print(r)
