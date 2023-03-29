from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import plotly.express as plt
import pandas as pd
from modules.FetchPortfolio import DeBankPortfolio

class PandasModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe """

    def __init__(self, dataframe=pd.DataFrame(), parent=None):
        QAbstractTableModel.__init__(self, parent)

        self.original_dataframe = dataframe.copy(deep=True)

        self._dataframe = self.convert_df_to_str(dataframe)

        self.paint_df = pd.DataFrame()

    def rowCount(self, parent=QModelIndex()) -> int:
        """ Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe)

        return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe.columns)
        return 0

    def data(self, index: QModelIndex, role=Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        elif role == Qt.BackgroundRole:
            if not self.paint_df.empty:
                colour = self.paint_df.iloc[index.row(), index.column()]

                if pd.notna(colour):
                    return colour

        '''elif role == Qt.BackgroundColorRole:
            colour = self.paint_df.iloc[index.row(), index.column()]

            if colour is not None:
                return colour'''

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._dataframe.columns[section])

            if orientation == Qt.Vertical:
                return str(self._dataframe.index[section])

        return None

class DefiPortfolioModel(PandasModel):
    def __init__(self, dataframe=pd.DataFrame(), parent=None):
        super().__init__(dataframe, parent)

        self.aggregation_level = "Position"

        self.table_colour_chart()

    def aggregation_level_change(self, aggregation_level):
        self.layoutAboutToBeChanged.emit()

        self.aggregation_level = aggregation_level

        if aggregation_level in ['Chain', 'Token', 'Dapp']:
            aggregated_series = self.original_dataframe.groupby(aggregation_level)['USD Value'].sum() / self.original_dataframe['USD Value'].sum()

            aggregated_series = aggregated_series.sort_values(ascending=False)
            aggregated_series = self.convert_df_to_str(aggregated_series)

            self._dataframe = pd.DataFrame(columns=aggregated_series.index, data=[aggregated_series.values])

        elif aggregation_level == 'Pool':
            self._dataframe = self.original_dataframe.groupby(['Chain', 'Dapp', 'Pool'])['USD Value'].sum().reset_index()
            self._dataframe['Weight'] = (self._dataframe['USD Value'] / self._dataframe['USD Value'].sum()) * 100
            self._dataframe = self._dataframe.sort_values(by='Weight', ascending=False)
            self._dataframe = self.convert_df_to_str(self._dataframe)

        elif aggregation_level == 'Position':
            self._dataframe = self.original_dataframe.copy(deep=True)

            self._dataframe = self.convert_df_to_str(self._dataframe)

        self.table_colour_chart()

        self.layoutChanged.emit()

    def date_change(self, date):
        self.layoutAboutToBeChanged.emit()

        path_root = r"C:\Users\lyons\OneDrive - Old Street Digital\Investment Files\Data Snapping\Raw Snaps\CIF Snap"

        date_tuple = date.getDate()

        date_formatted = f"{date_tuple[0]}-{str(date_tuple[1]).zfill(2)}-{str(date_tuple[2]).zfill(2)}"

        path = fr"{path_root}/{date_formatted}/CIF_debank.pkl"

        portfolio_snap = pd.read_pickle(path)

        portfolio_df = DeBankPortfolio(portfolio_snap).portfolio

        self.original_dataframe = portfolio_df.copy(deep=True)

        self.aggregation_level_change(self.aggregation_level)

        self.table_colour_chart()

        self.layoutChanged.emit()

    def convert_df_to_str(self, pandas_object):
        if isinstance(pandas_object, pd.DataFrame):
            if 'Position' in pandas_object.columns:
                pandas_object['Position'] = pandas_object['Position'].map(lambda x: "{:,}".format(round(x, 6)))
            if 'Price' in pandas_object.columns:
                pandas_object['Price'] = pandas_object['Price'].map(lambda x: "{:,}".format(round(x, 6)))
            if 'USD Value' in pandas_object.columns:
                pandas_object['USD Value'] = pandas_object['USD Value'].map(lambda x: "{:,}".format(round(x, 2)))
            if 'Weight' in pandas_object.columns:
                pandas_object['Weight'] = pandas_object['Weight'].map(lambda x: f"{str(round(x, 2))}%")

        elif isinstance(pandas_object, pd.Series):
            pandas_object = pandas_object * 100
            pandas_object = pandas_object.round(decimals=2)
            pandas_object = pandas_object.map(lambda x: f"{str(x)}%")

        return pandas_object

    def table_colour_chart(self):
        self.paint_df = pd.DataFrame(index=self._dataframe.index, columns=self._dataframe.columns)

        if self.aggregation_level == 'Position':
            return

        threshold = config['Portfolio'][self.aggregation_level]

        if 'Weight' in self._dataframe.columns:
            comparison_series = self._dataframe['Weight']
        else:
            comparison_series = pd.Series(index=self._dataframe.columns, data=self._dataframe.values[0])

        if isinstance(threshold, dict):
            if 'Weight' in self._dataframe.columns:
                comparison_values = self._dataframe[self.aggregation_level].map(threshold)
            else:
                comparison_values = pd.DataFrame(columns=self._dataframe.columns, index=self._dataframe.index)

                threshold_coins = comparison_values.columns[comparison_values.columns.isin(threshold.keys())]
                filtered_thresholds = {key: threshold[key] for key in threshold_coins}

                comparison_values.loc[:, threshold_coins] = list(filtered_thresholds.values())

            comparison_values = comparison_values.fillna(threshold['standard'])

            comparison_values = pd.Series(index=comparison_values.columns, data=comparison_values.values[0])

            comparison_values = comparison_values * 100
        else:
            comparison_values = threshold * 100

        comparison_series = pd.to_numeric(comparison_series.str.replace("%", ""))

        red_indices = (comparison_series > comparison_values)
        yellow_indices = (comparison_series > (comparison_values - 1))
        #yellow_indices = list(set(yellow_indices).difference(red_indices))

        if "Weight" in self.paint_df:
            self.paint_df.loc[yellow_indices, "Weight"] = QBrush(Qt.darkYellow)
            self.paint_df.loc[red_indices, "Weight"] = QBrush(Qt.red)
        else:
            #yellow_indices = yellow_indices.columns[yellow_indices.all()]
            #red_indices = red_indices.columns[red_indices.all()]

            self.paint_df.loc[:, yellow_indices] = QBrush(Qt.darkYellow)
            self.paint_df.loc[:, red_indices] = QBrush(Qt.red)

class TableView(QTableView):
    def __init__(self, *__args):
        super().__init__(*__args)

        #self.setColumnCount(6)
        #self.setHorizontalHeaderLabels(
        #    ['Chain', 'DApp', 'Asset', 'Position', 'Price', 'Market Value'])

        tableSizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        tableSizePolicy.setHorizontalStretch(0)
        tableSizePolicy.setVerticalStretch(0)
        tableSizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(tableSizePolicy)

        '''tablePalette = QPalette()
        brush = QBrush(QColor(221, 221, 221, 255))
        brush.setStyle(Qt.SolidPattern)
        tablePalette.setBrush(QPalette.Active, QPalette.WindowText, brush)
        brush1 = QBrush(QColor(0, 0, 0, 0))
        brush1.setStyle(Qt.SolidPattern)
        tablePalette.setBrush(QPalette.Active, QPalette.Button, brush1)
        tablePalette.setBrush(QPalette.Active, QPalette.Text, brush)
        tablePalette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        brush2 = QBrush(QColor(0, 0, 0, 255))
        brush2.setStyle(Qt.NoBrush)
        tablePalette.setBrush(QPalette.Active, QPalette.Base, brush2)
        tablePalette.setBrush(QPalette.Active, QPalette.Window, brush1)
        # if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        tablePalette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush)
        # endif
        tablePalette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        tablePalette.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        tablePalette.setBrush(QPalette.Inactive, QPalette.Text, brush)
        tablePalette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        brush3 = QBrush(QColor(0, 0, 0, 255))
        brush3.setStyle(Qt.NoBrush)
        tablePalette.setBrush(QPalette.Inactive, QPalette.Base, brush3)
        tablePalette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        # if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        tablePalette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush)
        # endif
        tablePalette.setBrush(QPalette.Disabled, QPalette.WindowText, brush)
        tablePalette.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        tablePalette.setBrush(QPalette.Disabled, QPalette.Text, brush)
        tablePalette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush)
        brush4 = QBrush(QColor(0, 0, 0, 255))
        brush4.setStyle(Qt.NoBrush)
        tablePalette.setBrush(QPalette.Disabled, QPalette.Base, brush4)
        tablePalette.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        # if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        tablePalette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush)
        # endif
        self.setPalette(tablePalette)'''

        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        self.setSortingEnabled(True)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setCascadingSectionResizes(True)
        self.horizontalHeader().setDefaultSectionSize(200)
        self.horizontalHeader().setStretchLastSection(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setCascadingSectionResizes(False)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setStretchLastSection(False)
