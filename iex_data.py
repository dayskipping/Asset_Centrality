import requests
import pandas as pd
import numpy as np
import datetime

class IEX():
    def __init__(self, securities=None, begin=None, end=datetime.datetime.now().date(), endpoint='https://api.iextrading.com/1.0/stock/market/batch'):
        self.securities = securities
        self.begin = begin
        self.end = end
        if begin != None:
            self.time_period = self.end - self.begin
        self.endpoint = endpoint

    @staticmethod
    def df_compiler():
        stocks = IEX()
        stocks.symbols_get('cs')
        company_df = stocks.company_info_get(['industry', 'sector'])
        company_df = pd.get_dummies(company_df, ['industry', 'sector'])
        shares_df = stocks.company_info_get(['sharesOutstanding'],'stats')
        # earnings_df = stocks.earnings_info_get(['actualEPS'])
        financials_df = stocks.financials_info_get('annual')
        prices_df = stocks.price_get('1y')
        average_price = prices_df.mean(axis=0).rename('avgPrice')
        df = company_df.join(financials_df).join(shares_df).join(average_price)
        df['marketCap'] = df['sharesOutstanding'] * df['avgPrice']
        df.drop(['sharesOutstanding', 'avgPrice'], axis=1, inplace=True)
        return df

    # single get request to API
    def _single_query(self, payload):
        response = requests.get(self.endpoint, params=payload)
        if response.status_code != 200:
            print('request unsuccessful')
        else:
            response_j = response.json()
        return response_j

    # function to step through list of symbols 'size' at a time
    def _chunker(self, seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    # function to replace None with 0
    def _replace_none(self, x):
        for i, val in enumerate(x):
            if val == None:
                x[i] = 0
        return x

    # query API for comprensive list of security symbols available
    def symbols_get(self, type=None, endpoint='https://api.iextrading.com/1.0/ref-data/symbols'):
        symbols = requests.get(endpoint).json()
        # Filter symbols to create list of common stocks only
        symbols_list = []
        if type == None:
            for sym in symbols:
                symbols_list.append(sym['symbol'])
        else:
            for sym in symbols:
                if sym['type'] == type:
                    symbols_list.append(sym['symbol'])
        self.securities = symbols_list

    # query API for company info and return df with tickers as index and columns as company info
    def company_info_get(self, parameters, cat='company'):
        symbol_dict = {}
        param_string = (', ').join(parameters)
        # securities = self.securities
        for group in self._chunker(self.securities, 100):
            payload = {'filter': param_string, 'types': cat, 'symbols':(', ').join(group)}
            response = self._single_query(payload)
            group_dict = {}
            for ticker in group:
                group_dict[ticker] =[response[ticker][cat][param]\
                for param in parameters]
            symbol_dict.update(group_dict)
        company_info_df = pd.DataFrame(columns=parameters, index=symbol_dict.keys(), data=list(symbol_dict.values()))
        return company_info_df


    def earnings_info_get(self, parameters, cat='earnings'):
        param_string = (', ').join(parameters)
        symbol_dict = {}
        for group in self._chunker(self.securities, 100):
            group_dict = {}
            payload = {'filter': param_string, 'types': cat, 'symbols':(', ').join(group)}
            response = self._single_query(payload)
            for ticker in group:
                try:
                    group_dict[ticker] =[dict[param]\
                    for param in parameters \
                    for dict in response[ticker][cat][cat]]
                except:
                    group_dict[ticker] = [np.nan]
            symbol_dict.update(group_dict)
        earnings_df = pd.DataFrame(columns=parameters*4, index=symbol_dict.keys(), data=list(symbol_dict.values()))
        return earnings_df


    def financials_info_get(self, period, cat='financials'):
        for ticker in self.securities:
            if ticker not in self.symbol_get('cs'):
                return ".securities attribute must be set to common stocks only"
        symbol_dict = {}
        for group in self._chunker(self.securities, 100):
            group_dict = {}
            payload = {'types': cat, 'symbols':(', ').join(group), 'period': period}
            response = self._single_query(payload)
            for ticker in group:
                try:
                    group_dict[ticker] = list(response[ticker][cat][cat][0].values())
                except:
                    group_dict[ticker] = [np.nan]
            symbol_dict.update(group_dict)
        financials_keys = list(response[ticker]['financials']['financials'][0].keys())
        financials_df = pd.DataFrame(index=symbol_dict.keys(), columns=financials_keys, data=list(symbol_dict.values()) )
        return financials_df

    def price_get(self, range, symbols=None, cat='chart'):
        if symbols:
            self.securities = symbols
        symbol_dict = {}
        for group in self._chunker(self.securities, 100):
            group_dict = {}
            payload = {'filter': 'close, date', 'types': cat, 'symbols': (', ').join(group), 'range': range}
            response = self._single_query(payload)
            for ticker in group:
                try:
                    closing_prices = {}
                    for dict in response[ticker][cat]:
                        closing_prices[dict['date']] = [dict['close']]
                    if closing_prices == {}:
                        group_dict[ticker] = [np.nan]
                    else:
                        group_dict[ticker] = closing_prices
                except:
                    group_dict[ticker] = [np.nan]
            symbol_dict.update(group_dict)
        price_df = pd.DataFrame()
        for k, v in symbol_dict.items():
            if v == [np.nan]:
                price_df[k] = np.nan
            else:
                join_df = pd.DataFrame(v).T
                join_df.columns = [k]
                price_df = price_df.join(join_df, how='outer')
        price_df.index = pd.to_datetime(price_df.index)
        return price_df

print('Is this main ?')

if __name__ == '__main__':

    print('This is is main')






    # Query IEX API for list of all supported symbols
    # endpoint = 'https://api.iextrading.com/1.0/ref-data/symbols'
    # symbols = requests.get(endpoint).json()
    # # Filter symbols to create list of common stocks only
    # stock_symbols = []
    # for sym in symbols:
    #     if sym['type'] == 'cs':
    #         stock_symbols.append(sym['symbol'])
    #
    # financials_group_list = []
    # endpoint_1 = 'https://api.iextrading.com/1.0/stock/market/batch'
    # for group in _chunker(stock_symbols, 100):
    #     params = {'types': 'financials', 'symbols': (', ').join(group), 'period': 'annual'}
    #     fin_group = _single_query(endpoint_1, params)
    #     financials_group_list.append(fin_group)
    #
    # financials_data_list = []
    # for group in financials_group_list:
    #     for stock in group:
    #         financials_data_list.append([group[stock]['financials'].values()])
    # # Create list of stocks that are missing financials data and list of lists of financials data for all others
    # new_list = []
    # missing_list = []
    # for i in range(len(financials_data_list)):
    #     fin_list = list(financials_data_list[i][0])
    #     if len(fin_list) == 0:
    #         missing_list.append(i)
    #     else:
    #         new_list.append(fin_list[1][0])
    # new_values = []
    # for dict in new_list:
    #     new_values.append(dict.values())
    # total_index = list(range(len(stock_symbols)))
    # # boolean index of stocks that have financials data
    # mask = [False if x in missing_list else True for x in total_index]
    # stocks_array = np.array(stock_symbols)[mask]
    # # Create final dataframe for all financials data
    # final_df = pd.DataFrame(index=stocks_array, columns=new_list[0].keys(), data=new_values)
    #
    # # Create list with stats and 1y historical prices
    # stats_list = []
    # price_list = []
    # for group in _chunker(stocks_array, 100):
    #     params = {'types': 'stats', 'symbols': (', ').join(group)}
    #     stats_group = _single_query(endpoint_1, params)
    #     stats_list.append(stats_group)
    #     params_p = {'types': 'chart', 'symbols': (', ').join(group), 'range': '1y'}
    #     price_group = _single_query(endpoint_1, params_p)
    #     price_list.append(price_group)
    # # Create lists with shares outstanding and average prices over 1y
    # shares_list = []
    # price_averages = []
    # for i, group in enumerate(_chunker(stocks_array, 100)):
    #     for stock in group:
    #         shares_list.append(stats_list[i][stock]['stats']['sharesOutstanding'])
    #         annual_prices = []
    #         for dict in price_list[i][stock]['chart']:
    #             annual_prices.append(dict['close'])
    #         if len(annual_prices) == 0:
    #             price_averages.append(0)
    #         else:
    #             price_averages.append(sum(annual_prices)/len(annual_prices))
    # shares_array = np.array(shares_list)
    # prices_array = np.array(price_averages)
    # final_df['marketCap'] = shares_array * prices_array
    #
    # final_df['totalLiabilities'].fillna(0,axis=0, inplace=True)
    # final_df['totalDebt'] = final_df['totalLiabilities']+final_df['totalDebt']
    # final_df.drop('totalLiabilities', inplace=True, axis=1)
    #
    # # Get company name, industry, and sector
    # company_params = 'companyName, industry, sector'
    # company_info = company_info_get(stock_symbols, company_params, 'company', endpoint_1)
    # df_cols = company_params.split(', ')
    # company_info_df = pd.DataFrame(company_info)
    # company_info_df = company_info_df.T
    # company_info_df.columns = df_cols
    #
    # # Get company earnings
    # earnings_params = 'actualEPS'
    # earnings_df = earnings_info_get(stocks_array, earnings_params,'earnings', endpoint_1)
    # earnings_df = pd.DataFrame(earnings_df).T
    # earnings_df.columns = ['earnings']
    #
    # # Get financials info
    # # financials_df, fin_keys = financials_info_get(stocks_array, 'financials', 'quarter', endpoint_1)
    # # financials_df = pd.DataFrame(financials_df).T
    # # financials_df.columns = list(fin_keys)[1:]
    #
    #
    # df = final_df.join(company_info_df).join(earnings_df)
    #
    # final_df.drop(['companyName'], inplace=True, axis=1)
    #
    # I_swear_final_df = pd.get_dummies(final_df, columns=['industry', 'sector'])
    # I_swear_final_df.dropna(inplace=True)
    # I_swear_final_df.to_csv('johnny_tables.csv', index=False)
