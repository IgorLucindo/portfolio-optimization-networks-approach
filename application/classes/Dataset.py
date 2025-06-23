import yfinance as yf
import pandas as pd
import os


class Dataset:
    """
    Class for getting instance from dataset of assets
    """
    def __init__(self, config):
        # Set dataset path
        self.config = config
        datasets_paths = {
            "m": "datasets/yahoo_finance/m",
            "l": "datasets/yahoo_finance/l"
        }
        self.datasets_path = datasets_paths[self.config['dataset_name']]
        os.makedirs(self.datasets_path, exist_ok=True)

        # Get daily prices from chosen dataset
        self.prices_dict = self._get_prices_dict()


    def _get_prices_dict(self):
        # Set date range
        date_range = ["2024-01-01", "2025-01-01"]

        # Get assets
        assets_dict = self._get_assets_dict()

        return {
            asset_type: self._get_partitions_data(asset_type, assets, date_range)
            for asset_type, assets in assets_dict.items()
        }


    def _get_assets_dict(self):
        assets_dict = {}

        match self.config['dataset_name']:
            case "m":
                assets_dict["bonds"] = ["AGG", "BND", "LQD", "TLT", "IEF", "SHY", "BSV", "BIV", "BLV", "JNK", "HYG", "SPAB", "SCHZ", "GOVT", "VGSH", "VGIT", "VGLT", "IGSB", "IGIB", "IGLB", "SHYG", "SPSB", "SPIB", "SPLB", "TFLO", "BIL", "SHV", "MINT", "JPST", "GBIL", "TIPX", "TIP", "SCHP", "VTIP", "STIP", "IGOV", "BWX", "BNDX", "EMB", "EMLC", "LEMB", "EBND", "TOTL", "FBND", "NUBD", "GVI", "SMMU", "VCSH", "VCLT", "VCIT", "VMBS", "MBSD", "SRLN", "HYLB", "HYGH", "IHY", "ISHG", "WIP", "CWB", "ANGL", "FALN", "FLOT", "FLTR", "BOND", "FIBR", "GNMA", "TFI", "HYD", "PZA", "MUB", "SUB", "SHM", "CMF", "NYF", "VTEB", "PAB", "VUSB", "ICSH", "NEAR", "FTSD", "ULST", "SPSK", "IBND", "HYS", "HYXU", "VWOB", "CEMB", "IAGG", "QLTA", "PLW", "EDV", "ZROZ", "GOVZ", "USFR", "RIGS", "FLRN", "VRIG", "TUA", "FTGC"]
                assets_dict["stocks"] = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA","AVGO", "LLY", "JPM", "UNH", "V", "JNJ", "XOM", "WMT", "MA", "PG", "HD", "CVX", "COST", "MRK", "ABBV", "PEP", "PFE", "KO", "INTC", "CSCO", "TMO", "ORCL", "ACN", "ADBE", "CRM", "CMCSA", "MCD", "TXN", "DHR", "NKE", "BMY", "NEE", "RTX", "LMT", "GE", "INTU", "QCOM", "SBUX", "AMGN", "LOW", "CAT", "AXP", "CVS", "CHTR", "GILD", "BA", "MDT", "GM", "HON", "MMM", "CL", "MDLZ", "MO", "SO", "GS", "DIS", "IBM", "SCHW", "BK", "MS", "C", "WFC", "USB", "PNC", "TFC", "COF", "AIG", "MET", "PRU", "TRV", "PGR", "ALL", "CB", "AON", "MMC", "CI", "HUM", "CNC", "UPS", "FDX", "UNP", "NSC", "CSX", "AMT", "CCI", "EQIX", "DLR", "SPG", "PSA", "O"]
                assets_dict["commodities"] = ["DBC", "PDBC", "USCI", "GSG", "COMT", "BCI", "DJP", "CMDY", "USO", "BNO", "UCO", "SCO", "UNG", "BOIL", "KOLD", "GLD", "IAU", "SGOL", "BAR", "SLV", "SIVR", "PLTM", "PPLT", "PALL", "CPER", "CORN", "WEAT", "SOYB", "CANE", "UGA", "DBB", "FTGC", "XOP", "XME", "PICK", "REMX", "URA"]
                assets_dict["cryptos"] = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "AVAX-USD", "TON11419-USD", "SHIB-USD", "DOT-USD", "TRX-USD", "LINK-USD", "MATIC-USD", "BCH-USD", "LTC-USD", "UNI7083-USD", "ICP-USD", "NEAR-USD", "ETC-USD", "XLM-USD", "APT21794-USD", "IMX10603-USD", "FIL-USD", "INJ-USD", "HBAR-USD", "VET-USD", "MKR-USD", "ARB11841-USD", "QNT-USD", "RUNE-USD", "LDO-USD", "AAVE-USD", "EGLD-USD", "STX-USD", "SAND-USD", "AXS-USD", "XTZ-USD", "KAS-USD", "XMR-USD", "THETA-USD", "SNX-USD", "MANA-USD", "CRV-USD", "CHZ-USD", "ZEC-USD", "ENS-USD", "DYDX-USD"]
            case "l":
                df = pd.read_excel(self.datasets_path + "/tickers.xlsx")
                assets_dict["stocks"] = df['STOCKS'].dropna().astype(str).tolist()
                # assets_dict["etfs"] = df['ETF'].dropna().astype(str).tolist()

        return assets_dict
    

    def _get_partitions_data(self, asset_type, assets, date_range):
        data = {}
        number_of_assets = self.config['assets']['range']

        for k in range(self.config['assets']['#partitions']):
            # Set collumns range and partion name
            cols_start = k * number_of_assets
            cols_end = min((k+1) * number_of_assets, len(assets))
            cols_range = range(cols_start, cols_end)
            partition_name = f"{cols_start} - {cols_end-1}"

            # Get data for each partition
            data[partition_name] = self._get_data_yfinance(asset_type, assets, date_range, cols_range)

        return data
    

    def _get_data_yfinance(self, asset_type, assets, date_range, cols_range):
        """
        Return price data Loaded from dataset or downloaded and saved
        """
        asset_path = self.datasets_path + "/" + asset_type + ".csv"

        if os.path.exists(asset_path):
            price_data = pd.read_csv(asset_path, index_col=0, parse_dates=True)
            price_data = price_data.iloc[:, cols_range]
            assets = price_data.iloc[0].dropna().index.tolist()
        else:
            price_data = yf.download(assets, start=date_range[0], end=date_range[1])["Close"]
            price_data.to_csv(asset_path)
            
        price_data = price_data.dropna()

        return [assets, price_data.to_numpy()]