import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Constants for result path and file name
RESULT_PATH = '/home/kei/naver_news_crawling/crawling_result/'
EXCEL_FILE_FORMAT = '{year}-{month}-{day} {hour} hour {minute} minute {second} second merging.xlsx'

class NaverNewsCrawler:

    def __init__(self, max_pages, query, sort, start_date, end_date):
        self.max_pages = max_pages
        self.query = query
        self.sort = sort
        self.start_date = start_date
        self.end_date = end_date
        self.result = {
            "Article title": [],
            "Media": [],
            "Date": [],
            "URL": [],
            "Content summary": []
        }

    def run(self):
        for page in range(1, int(self.max_pages)*10+1, 10):
            url = self.build_url(page)
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            self.parse_page(soup)
        
        self.save_to_excel()

    def build_url(self, page):
        formatted_start_date = self.start_date.replace(".", "")
        formatted_end_date = self.end_date.replace(".", "")
        return f"https://search.naver.com/search.naver?where=news&query={self.query}&sort={self.sort}&ds={self.start_date}&de={self.end_date}&nso=so%3Ar%2Cp%3Afrom{formatted_start_date}to{formatted_end_date}%2Ca%3A&start={page}"

    def parse_page(self, soup):
        titles_and_links = self.extract_titles_and_links(soup)
        sources = self.extract_sources(soup)
        dates = self.extract_dates(soup)
        summaries = self.extract_summaries(soup)
        
        max_length = max(len(titles_and_links), len(sources), len(dates), len(summaries))
        
        # Ensure all lists are of the same length by appending 'N/A'
        while len(titles_and_links) < max_length:
            titles_and_links.append(('N/A', 'N/A'))
        while len(sources) < max_length:
            sources.append('N/A')
        while len(dates) < max_length:
            dates.append('N/A')
        while len(summaries) < max_length:
            summaries.append('N/A')
        
        # Append extracted data to the result dictionary
        for (title, link), source, date, summary in zip(titles_and_links, sources, dates, summaries):
            self.result["Article title"].append(title)
            self.result["URL"].append(link)
            self.result["Media"].append(source)
            self.result["Date"].append(date)
            self.result["Content summary"].append(summary)

    def extract_titles_and_links(self, soup):
        titles_and_links = []
        atags = soup.select('.news_tit')
        for atag in atags:
            titles_and_links.append((atag.text, atag['href']))
        return titles_and_links

    def extract_sources(self, soup):
        sources = []
        source_tags = soup.select('.info_group > .press')
        for source in source_tags:
            sources.append(source.text)
        return sources

    def extract_dates(self, soup):
        dates = []
        date_tags = soup.select('.info_group > span.info')
        for date in date_tags:
            if "If" not in date.text:
                dates.append(date.text)
        return dates

    def extract_summaries(self, soup):
        summaries = []
        summary_tags = soup.select('.news_dsc')
        for summary in summary_tags:
            cleaned_summary = self.clean_summary(summary)
            summaries.append(cleaned_summary)
        return summaries

    @staticmethod
    def clean_summary(contents):
        first_clean = re.sub('<dl>.*?</a> </div> </dd> <dd>', '', str(contents)).strip()
        second_clean = re.sub('<ul class="relation_lst">.*?</dd>', '', first_clean).strip()
        final_clean = re.sub('<.+?>', '', second_clean).strip()
        return final_clean

    def save_to_excel(self):
        now = datetime.now()
        file_name = EXCEL_FILE_FORMAT.format(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=now.minute, second=now.second)
        df = pd.DataFrame(self.result)
        df.to_excel(f"{RESULT_PATH}{file_name}", sheet_name='sheet1')


if __name__ == "__main__":
    max_pages = input("Enter the maximum number of pages to crawl: ")
    query = input("Enter search term: ")
    sort = input("Enter news search method (relevance = 0, latest = 1, oldest = 2): ")
    start_date = input("Enter start date (2023.10.16):")
    end_date = input("Enter end date (2023.10.17):")

    crawler = NaverNewsCrawler(max_pages, query, sort, start_date, end_date)
    crawler.run()
