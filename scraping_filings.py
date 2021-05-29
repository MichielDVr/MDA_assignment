class filings:
    def __init__(self, path, download==True):
        self.path = path
        self.download = download
    # if True then download all filings of Edgar from 2019 onwards
    if self.download == True:
            edgar.download_index(path, 2019, skip_all_present_except_last=False)
        self.quarters = ['2019 Q1', '2019 Q2', '2019 Q3', '2019 Q4', '2020 Q1', '2020 Q2', '2020 Q3', '2020 Q4',
                         '2021 Q1']
        self.biggestComp = []
        self.compAllQ = []

        self.urls = []
        self.filings = []
        self.run()

    def run(self):
        'methods to get all 13F-HR filings, get biggest investment comp and make selection'
        self.select_compAllQ()
        self.scrape_biggestComp()
        self.select_biggestComp()
        self.run_parser()

    def get_filingIndex(self, path):
        'get tuple of company name and url of index pages of 13F-HR filings'
        with open(path, 'r') as file:
            tsvreader = csv.reader(file, delimiter="|")
            filings = []
            for line in tsvreader:
                # only 13F-HR type
                if line[1:][1] == '13F-HR':
                    adress = line[-1]
                    # add common url
                    url = 'https://www.sec.gov/Archives/' + adress
                    # name company
                    company = line[1]
                    filings.append((company.lower(), url))
        return filings

    def get_filingIndexAll(self):
        ''' get dict with tuple of company-url for every quarter'''
        company_url = {}
        for quarter in self.quarters:
            company_url[quarter] = self.get_filingIndex(quarter.partition(" ")[0] + '-' + 'QTR' + quarter[-1] + '.tsv')
        return company_url

    def get_compName(self):
        ''' get dict with name of companies for every quarter'''
        comp = {}
        for quarter in self.quarters:
            comp[quarter] = [i[0] for i in
                             self.get_filingIndex(quarter.partition(" ")[0] + '-' + 'QTR' + quarter[-1] + '.tsv')]
        return comp

    def select_compAllQ(self):
        '''select companies that have filings in every quarter 2019-2021'''
        comp = self.get_compName()
        comp_AllQ = [i for i in
                     comp['2019 Q1'] and comp['2019 Q2'] and comp['2019 Q3'] and comp['2019 Q4'] and comp['2020 Q1'] and
                     comp['2020 Q2'] and comp['2020 Q3'] and comp['2020 Q4'] and comp['2021 Q1']]
        self.compAllQ = comp_AllQ

    def scrape_biggestComp(self):
        '''scrape a list of largest mutual fund companies in the US (140 entries)'''
        URL = 'https://mutualfunddirectory.org/latest-directory-ranking-here/'
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find('table', class_="tablepress-id-109")
        for company in table.find_all('tbody'):
            rows = company.find_all('tr')
            companies = []
            for row in rows:
                companies.append(row.find('td', class_="column-2").text)

        companies = companies[:-1]
        self.biggestComp = [i.lower() for i in companies]

    def select_biggestComp(self):
        '''from the set of filings, select only those administered by largest companies
           Returns urls of filing-pages to be used in parser'''
        allfilings = self.get_filingIndexAll()
        urls_list = {}
        for quarter in self.quarters:
            urls = []
            companies_Q = [i for i in allfilings[quarter] if i[0] in self.compAllQ]
            for company in companies_Q:
                if len(company[0].split()) > 1:
                    # comp names can be slightly different on filing and list biggest comp
                    ## look for comp names where first two words are the same
                    if company[0].split()[0] in self.biggestComp or company[0].split()[1] in self.biggestComp:
                        urls.append(company[1])
                else:
                    # if comp name is 1 word
                    if company[0].split()[0] in self.biggestComp:
                        urls.append(company[1])
            urls_list[quarter] = urls
        self.urls = urls_list

    # def sameNumberComp(self, urls_list):
    #     ''' select only the biggest companies that have filings in every quarter'''
    #     unique_companies=[urls_list[1][j].split('data/')[1].split('/')[0] for j in range(len(urls_list[1]))]
    #     unique_urls_list=[]
    #     for i in range(len(urls_list)):
    #         unique_urls=[urls_list[i][j] for j in range(len(urls_list[i])) if urls_list[i][j].split('data/')[1].split('/')[0] in unique_companies]
    #         unique_urls_list.append(unique_urls)
    #     return unique_urls_list

    def parser(self, urls):
        '''Takes URL's of the filing index page on Edgar Archives and scrapes html information table
        Returns dataframe of holdings of 20 companies by concatenating the filing tables
        NOTE When User Agent is used to often, Edgar will not allow entrance to database. In that case, one needs to change User Agent '''
        df = []
        for url in urls:
            my_header = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
            page = requests.get(url, headers=my_header)
            data = page.text
            soup = BeautifulSoup(data, "lxml")
            result = soup.find_all('div', attrs={'class': 'formGrouping'})[0]
            date = result.find('div', attrs={'class': 'info'}).text
            index = soup.find('div', {'id': 'secNum'}).text.replace('SEC Accession No. ', '').replace('\n', '')
            entityName = soup.find('span', attrs={'class': "companyName"}).text
            entityName = entityName.partition("(Filer)")[0]

            # get third hyperlink on page which directs to info table
            table_link = soup.find('table', attrs={'class': 'tableFile'})
            table_link = table_link.find_all('a')
            table_link = table_link[2]
            identifier = table_link.get('href')
            url = 'https://www.sec.gov' + identifier

            # get CIK number from URL
            cik_company = url.split('data/')[1].split('/')[0]

            # parse html table to dataframe
            ## retry when 'https forbidden' error is raised, until page can be scraped successfully
            DF_13F = None
            while DF_13F is None:
                try:
                    DF_13F = pd.read_html(url)
                    DF_13F = DF_13F[-1]
                    DF_13F = DF_13F.iloc[2:]
                    new_header = DF_13F.iloc[0]
                    DF_13F.columns = new_header
                    DF_13F = DF_13F.iloc[2:]
                    DF_13F['date_reported'] = date
                    DF_13F['CIK'] = cik_company
                    DF_13F['filing index'] = index
                    DF_13F['Entity name'] = entityName

                    # Get entity name from CIK code from list of all funds
                    # DF_13F['Entity Name'] = df_MF['Entity Name'].loc[df_MF['CIK Number'] == cik_company].values

                    DF_13F = DF_13F[
                        ['filing index', 'date_reported', 'NAME OF ISSUER', 'TITLE OF CLASS', 'CUSIP', '(x$1000)',
                         'PRN AMT', 'PRN', 'CIK', 'Entity name']]
                    df.append(DF_13F)
                    print('Filing found for cik %s at %s' % (cik_company, url))

                except:
                    print('Retry, could not parse cik %s at: %s' % (cik_company, url))
                    pass
            return pd.concat(df)

    def run_parser(self):
        'Save parsed filings in dict of dataframes for every quarter, and pickle it -> load when making graph'
        df_All = {j: self.parser(self.urls[j]) for j in self.quarters}
        with open(self.path + os.sep + 'df_All', "wb") as f:
            pickle.dump(df_All, f)
            f.close()
        for quarter in self.quarters:
            adj = self.adjacency_matrix(df_All[quarter])
        with open(self.path + os.sep + 'adj', "wb") as f:
            pickle.dump(adj, f)
            f.close()


    def adjacency_matrix(df):
        '''compute adjacency matrix of investment companies based on value of common holdings'''
        dummies = pd.get_dummies(df['CUSIP']).astype(float)
        weights = dummies.T * np.asarray(df['(x$1000)']).astype(float)
        df_ = pd.concat([df[['CIK']], weights.T], axis=1)
        weights = df_.groupby(['CIK']).sum()
        v = np.dot(weights, weights.T)
        v = np.tril(v, -1)
        return v


filings(path).urls
