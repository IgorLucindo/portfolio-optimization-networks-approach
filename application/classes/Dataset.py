import yfinance as yf
import pandas as pd
import os


class Dataset:
    """
    Class for getting instance from dataset of assets
    """
    def __init__(self, dataset, num_of_asset_types=4):
        # Set dataset path
        datasets_paths = {
            "yahoo_finance": "datasets/yahoo_finance"
        }
        self.datasets_path = datasets_paths[dataset]
        os.makedirs(self.datasets_path, exist_ok=True)

        # Get daily prices from chosen dataset
        self.prices_dict = self._get_financial_assets(num_of_asset_types)


    def _get_financial_assets(self, num_of_asset_types=4):
        # Set date range
        date_range = ["2024-01-01", "2025-01-01"]

        # Get assets
        assets_dict = self._get_assets_dict(num_of_asset_types)

        return {
            asset_type: [assets, self._get_price_data_yfinance(asset_type, assets, date_range)]
            for asset_type, assets in assets_dict.items()
        }


    def _get_assets_dict(self, num_of_asset_types=4):
        bonds = [
            "AGG", "BND", "LQD", "TLT", "IEF", "SHY", "BSV", "BIV", "BLV", "JNK",
            "HYG", "SPAB", "SCHZ", "GOVT", "VGSH", "VGIT", "VGLT", "IGSB", "IGIB", "IGLB",
            "SHYG", "SPSB", "SPIB", "SPLB", "TFLO", "BIL", "SHV", "MINT", "JPST", "GBIL",
            "TIPX", "TIP", "SCHP", "VTIP", "STIP", "IGOV", "BWX", "BNDX", "EMB",
            "EMLC", "LEMB", "EBND", "TOTL", "FBND", "NUBD", "GVI", "SMMU", "VCSH", "VCLT",
            "VCIT", "VMBS", "MBSD", "SRLN", "HYLB", "HYGH", "IHY", "ISHG", "WIP", "CWB",
            "ANGL", "FALN", "FLOT", "FLTR", "BOND", "FIBR", "GNMA", "TFI", "HYD", "PZA",
            "MUB", "SUB", "SHM", "CMF", "NYF", "VTEB", "PAB", "VUSB", "ICSH", "NEAR",
            "FTSD", "ULST", "SPSK", "IBND", "HYS", "HYXU", "VWOB", "CEMB", "IAGG", "QLTA",
            "PLW", "EDV", "ZROZ", "GOVZ", "USFR", "RIGS", "FLRN", "VRIG", "TUA", "FTGC"
        ]

        stocks = [
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA","AVGO",
            "LLY", "JPM", "UNH", "V", "JNJ", "XOM", "WMT", "MA", "PG", "HD",
            "CVX", "COST", "MRK", "ABBV", "PEP", "PFE", "KO", "INTC", "CSCO", "TMO",
            "ORCL", "ACN", "ADBE", "CRM", "CMCSA", "MCD", "TXN", "DHR", "NKE", "BMY",
            "NEE", "RTX", "LMT", "GE", "INTU", "QCOM", "SBUX", "AMGN", "LOW", "CAT",
            "AXP", "CVS", "CHTR", "GILD", "BA", "MDT", "GM", "HON", "MMM", "CL",
            "MDLZ", "MO", "SO", "GS", "DIS", "IBM", "SCHW", "BK", "MS", "C",
            "WFC", "USB", "PNC", "TFC", "COF", "AIG", "MET", "PRU", "TRV", "PGR",
            "ALL", "CB", "AON", "MMC", "CI", "HUM", "CNC", "UPS", "FDX",
            "UNP", "NSC", "CSX", "AMT", "CCI", "EQIX", "DLR", "SPG", "PSA", "O"
        ]

        commodities = [
            "DBC", "PDBC", "USCI", "GSG", "COMT", "BCI", "DJP", "CMDY", "USO", "BNO",
            "UCO", "SCO", "UNG", "BOIL", "KOLD", "GLD", "IAU", "SGOL", "BAR",
            "SLV", "SIVR", "PLTM", "PPLT", "PALL", "CPER", "CORN", "WEAT", "SOYB",
            "CANE", "UGA", "DBB", "FTGC", "XOP", "XME", "PICK", "REMX", "URA"
        ]

        cryptos = [
            "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "AVAX-USD", "TON11419-USD", "SHIB-USD",
            "DOT-USD", "TRX-USD", "LINK-USD", "MATIC-USD", "BCH-USD", "LTC-USD", "UNI7083-USD", "ICP-USD", "NEAR-USD", "ETC-USD",
            "XLM-USD", "APT21794-USD", "IMX10603-USD", "FIL-USD", "INJ-USD", "HBAR-USD", "VET-USD", "MKR-USD", "ARB11841-USD",
            "QNT-USD", "RUNE-USD", "LDO-USD", "AAVE-USD", "EGLD-USD", "STX-USD", "SAND-USD", "AXS-USD", "XTZ-USD",
            "KAS-USD", "XMR-USD", "THETA-USD", "SNX-USD", "MANA-USD", "CRV-USD", "CHZ-USD", "ZEC-USD", "ENS-USD", "DYDX-USD"
        ]

        assets_dict = {
            "bonds": bonds,
            "stocks": stocks,
            "commodities": commodities,
            "cryptos": cryptos
        }

        return dict(list(assets_dict.items())[:num_of_asset_types])
    

    def _get_price_data_yfinance(self, asset_type, assets, date_range):
        """
        Return price data Loaded from dataset or downloaded and saved
        """
        asset_path = self.datasets_path + "/" + asset_type + ".csv"

        if os.path.exists(asset_path):
            price_data = pd.read_csv(asset_path, index_col=0, parse_dates=True)
        else:
            price_data = yf.download(assets, start=date_range[0], end=date_range[1])["Close"]
            price_data.to_csv(asset_path)
            
        price_data = price_data.dropna()

        return price_data.to_numpy()