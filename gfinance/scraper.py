import re
import requests
import json
from bs4 import BeautifulSoup

def google_sector_report():
    """
    This function returns a JSON object containing the sector summary data from Google Finance.
    If an error occured, no exception is raised but the JSON returned has 'status' set as 'BAD'.
    """
    try:
        response = requests.get('https://www.google.com/finance')
        response.raise_for_status()

        result={}

        page_data_soup = BeautifulSoup(response.content,'lxml')

        list_sector = [x for x in list(page_data_soup.find('div',id='secperf').find('table').children) if x!='\n'][1:]
        
        for element in list_sector:
            change_rate =float(re.sub('[%]','',element.find('span',{'class':['chr','chg','chb']}).text))

            element_response = requests.get("https://www.google.com"+element.find('a').get('href'))
            element_response.raise_for_status()
            element_soup = BeautifulSoup(element_response.content,'lxml')

            sector_name = element_soup.find('div',{'class':'appbar-hide'}).find('h3').text.strip()
            
            top=None
            worst=None
            big_gain={"equity": "", "change": None}
            big_lose={"equity": "", "change": None}
            
            if('Gainers' in element_soup.find('table',{'class':'topmovers'}).findAll('tr')[0].find('b').get_text()):
                top = element_soup.find('table',{'class':'topmovers'}).findAll('tr')[1]
            if 'Losers' in element_soup.find('table',{'class':'topmovers'}).findAll('tr')[6].find('b').get_text():
                worst = element_soup.find('table',{'class':'topmovers'}).findAll('tr')[7]
            elif 'Losers' in element_soup.find('table',{'class':'topmovers'}).findAll('tr')[0].find('b').get_text():
                worst = element_soup.find('table',{'class':'topmovers'}).findAll('tr')[1]
            if top is not None:
                big_gain={
                    'change': float(re.sub('[()%]', '', top.findAll('span',{'class':['chr','chg','chb']})[1].get_text())),
                    'equity': top.findAll('a')[0].get_text()
                }
            if worst is not None:
                big_lose={
                    'change': float(re.sub('[()%]', '', worst.findAll('span',{'class':['chr','chg','chb']})[1].get_text())),
                    'equity': worst.findAll('a')[0].get_text()
                }
            sector={
                'change':change_rate,
                'biggest_gainer':big_gain,
                'biggest_loser':big_lose
            }
            result[sector_name]=sector
        return json.dumps({'status':'GOOD','result':result})

    except (KeyboardInterrupt, SystemExit):
        raise

    except Exception as err:
        print(err)
        return json.dumps({'status':'BAD','result':{}})