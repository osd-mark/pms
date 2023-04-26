# -*- coding: utf-8 -*-
import numpy

################################################################################
## Form generated from reading UI file 'maingnxZcz.ui'
##
## Created by: Qt User Interface Compiler version 6.0.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
#from PyQt5 import QtWebEngineWidgets

# from matplotlib.backends.backend_qt5agg import FigureCanvas
# from matplotlib.figure import Figure

#import pyqtgraph as pg
#import plotly.graph_objects as go
#import plotly
#import plotly.express as px
import pandas as pd
from modules.FetchPortfolio import DeBankPortfolio, DebankPortfolioTimeSeries, PortfolioTimeSeries
from .resources_rc import *
import yaml

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib as mpl
#import seaborn as sns
#import matplotlib.pyplot as plt

global config

with open("config.yaml", "r") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

class CalendarSelectorWidget(QDateEdit):
    def __init__(self, start_date, parent=None):
        super().__init__(parent=parent)

        self.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.setCalendarPopup(True)

        calendar = self.calendarWidget()
        weekday_format = calendar.weekdayTextFormat(Qt.Monday)
        calendar.setWeekdayTextFormat(Qt.Saturday, weekday_format)
        calendar.setWeekdayTextFormat(Qt.Sunday, weekday_format)
        calendar.setGridVisible(True)

        self.calendar = calendar

        self.setDate(QDate.currentDate())
        self.setMaximumDate(QDate.currentDate())
        self.setMinimumDate(start_date)

class PandasModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe """

    def __init__(self, dataframe=pd.DataFrame(), parent=None):
        QAbstractTableModel.__init__(self, parent)

        #self.original_dataframe = dataframe.copy(deep=True)

        self._dataframe = self.convert_df_to_str(dataframe)

        self.paint_df = pd.DataFrame()
        self.tool_tip_df = pd.DataFrame()

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

        elif role == Qt.ForegroundRole:
            if not self.paint_df.empty:
                colour = self.paint_df.iloc[index.row(), index.column()]

                if pd.notna(colour):
                    return colour

        if role == Qt.ToolTipRole:
            if not self.tool_tip_df.empty:
                tip = self.tool_tip_df.iloc[index.row(), index.column()]

                if pd.notna(tip):
                    return tip

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
    def __init__(self, portfolio_time_series, parent=None):
        self.portfolio_time_series = portfolio_time_series
        #self.debank_portfolio = self.portfolio_time_series.daily_portfolio_object
        self.debank_portfolio = DeBankPortfolio()
        self.debank_portfolio.sort_small_balances()
        dataframe = self.debank_portfolio.get_fund_assets()

        super().__init__(dataframe, parent)

        self.aggregation_level = "Position"

        self.table_colour_chart()
        self.set_tool_tip()

    def aggregation_level_change(self, aggregation_level):
        self.layoutAboutToBeChanged.emit()

        self.aggregation_level = aggregation_level

        if aggregation_level in ['Chain', 'Token', 'Dapp']:
            aggregated_series = self.debank_portfolio.get_aggregated_weights(aggregation_level)

            aggregated_series = aggregated_series.sort_values(ascending=False)

            aggregated_series = self.convert_df_to_str(aggregated_series)

            self._dataframe = pd.DataFrame(columns=aggregated_series.index, data=[aggregated_series.values])

        else:
            if aggregation_level in ['Position']:
                self._dataframe = self.debank_portfolio.portfolio.copy(deep=True)
            else:
                self._dataframe = self.debank_portfolio.get_aggregated_weights(aggregation_level)

                self._dataframe = self._dataframe.sort_values(by='Weight', ascending=False)

            self._dataframe = self.convert_df_to_str(self._dataframe)

        self.table_colour_chart()
        self.set_tool_tip()

        self.layoutChanged.emit()

    def date_change(self, date):
        self.layoutAboutToBeChanged.emit()

        date_tuple = date.getDate()

        date_formatted = f"{date_tuple[0]}-{str(date_tuple[1]).zfill(2)}-{str(date_tuple[2]).zfill(2)}"

        self.debank_portfolio = self.portfolio_time_series.daily_portfolio_objects[date_formatted]
        self.debank_portfolio.sort_small_balances()

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

        if self.aggregation_level in ['Position']:
            return

        threshold = config['Portfolio']['Limits']['Values'][self.aggregation_level]

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
            self.paint_df.loc[yellow_indices, "Weight"] = QColor('yellow')
            self.paint_df.loc[red_indices, "Weight"] = QColor('red')
        else:
            self.paint_df.loc[:, yellow_indices] = QColor('yellow')
            self.paint_df.loc[:, red_indices] = QColor('red')

    def set_tool_tip(self):
        self.tool_tip_df = pd.DataFrame(columns=self._dataframe.columns, index=self._dataframe.index)

        if self.aggregation_level == 'Position':
            return

        reasons = config['Portfolio']['Limits']['Reason'][self.aggregation_level]
        limits = config['Portfolio']['Limits']['Values'][self.aggregation_level]

        if isinstance(reasons, dict):
            if 'Weight' in self._dataframe.columns:
                tool_tip_hints = self._dataframe[self.aggregation_level].map(reasons + f"{limits * 100}%")
            else:
                tool_tip_hints = pd.DataFrame(columns=self._dataframe.columns, index=self._dataframe.index)

                specific_reason_coins = tool_tip_hints.columns[tool_tip_hints.columns.isin(reasons.keys())]
                filtered_specific_reason_coins = {key: reasons[key] + f"{int(limits[key] * 100)}%" for key in specific_reason_coins}

                tool_tip_hints.loc[:, specific_reason_coins] = list(filtered_specific_reason_coins.values())

            tool_tip_hints = tool_tip_hints.fillna(reasons['standard'] + f"{int(limits['standard'] * 100)}%")

            #tool_tip_hints = pd.Series(index=tool_tip_hints.columns, data=tool_tip_hints.values[0])

        else:
            tool_tip_hints = reasons + f"{int(limits * 100)}%"

        if "Weight" in self.tool_tip_df:
            self.tool_tip_df.loc[:, "Weight"] = tool_tip_hints
        else:
            self.tool_tip_df = tool_tip_hints

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
        #self.setSelectionBehavior(QAbstractItemView.SelectRows)
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

class StyledGraphWidget(FigureCanvas):
    def __init__(self, parent=None):
        super().__init__(Figure())
        self.setParent = parent

        ax = self.figure.subplots()

        ax.spines["top"].set_alpha(0.0)
        ax.spines["bottom"].set_alpha(0.3)
        ax.spines["right"].set_alpha(0.0)
        ax.spines["left"].set_alpha(0.3)

        ax.spines['bottom'].set_color("#00CE7C")
        ax.spines['left'].set_color("#00CE7C")
        ax.tick_params(axis='x', colors="#00CE7C")
        ax.tick_params(axis='y', colors="#00CE7C")

        ax.grid(axis='both', alpha=0.3)

        ax.set_facecolor("#282C34")#21252B
        self.figure.patch.set_facecolor("#282C34")#21252B

        self.ax = ax

        self.annot = self.ax.annotate("x", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)

class PerformanceGraphWidget(StyledGraphWidget):
    def __init__(self, portfolio_ts=DebankPortfolioTimeSeries(), parent=None):
        super().__init__(parent=parent)

        self.portfolio_ts = portfolio_ts

        portfolio_dates = sorted(list(set(self.portfolio_ts.portfolio['Date'])))

        self.selectors_dict = {'from_date': portfolio_dates[0],
                               'to_date': portfolio_dates[-1],
                               'rolling_window': 1, 'annualised': False, 'returns': False,
                               'peg_usdc': False}

        self.mpl_connect("motion_notify_event", self.hover)

        self.plot_ts()

    def plot_ts(self):
        if self.selectors_dict['returns']:
            ts = self.portfolio_ts.get_return_series(rolling_window=self.selectors_dict['rolling_window'],
                                                     annualised=self.selectors_dict['annualised'],
                                                     peg_usdc_to_par=self.selectors_dict['peg_usdc'])
        else:
            ts = self.portfolio_ts.get_nav_series(peg_usdc_to_par=self.selectors_dict['peg_usdc'])

        ts = ts.loc[(ts.index >= self.selectors_dict['from_date']) & (ts.index <= self.selectors_dict['to_date'])]

        y = ts.name
        x = ts.index.name

        ts = ts.reset_index()

        self.ax.clear()
        self.ax.grid(axis='both', alpha=0.3)
        self.ax.set_xlabel(x, color="#00CE7C")
        self.ax.set_ylabel(y, color="#00CE7C")

        self.plt = self.ax.plot(ts[x], ts[y], color="#00CE7C")

        #self.plt[0]()

        self.ax.set_xticklabels(self.ax.get_xticklabels(), rotation=40, ha="right")
        self.ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.2f}'))
        self.figure.tight_layout()

        self.draw()

    def hover(self, event):
        line, = self.plt
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            cont, ind = line.contains(event)
            if cont:
                self.update_annot(ind, line)
                self.annot.set_visible(True)

                print("event.xdata", event.xdata)
                print("event.ydata", event.ydata)
                print("event.inaxes", event.inaxes)
                print("x", event.x)
                print("y", event.y)

                self.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.figure.canvas.draw_idle()

    def update_annot(self, ind, line):
        x, y = line.get_data()
        self.annot.xy = (x[ind["ind"][0]], y[ind["ind"][0]])
        #text = "{}, {}".format(" ".join(list(map(str, ind["ind"]))),
        #                       " ".join([names[n] for n in ind["ind"]]))
        text = "{}".format(y[ind["ind"][0]]) #x[ind["ind"][0]],
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)

    def on_plot_hover(self, event):
        # Iterating over each data member plotted
        for curve in self.ax.get_lines():
            # Searching which data member corresponds to current mouse position
            if curve.contains(event)[0]:
                print("over %s" % curve.get_gid())

    def changed_from_date(self, date):
        self.selectors_dict['from_date'] = pd.to_datetime(date.toPyDate())

        self.plot_ts()

    def changed_to_date(self, date):
        self.selectors_dict['to_date'] = pd.to_datetime(date.toPyDate())

        self.plot_ts()

    def changed_rolling_avg_window(self, window):
        self.selectors_dict['rolling_window'] = int(window)

        self.plot_ts()

    def changed_returns_checkbox(self, checked_state):
        self.selectors_dict['returns'] = checked_state

        self.plot_ts()

    def changed_annualised_checkbox(self, checked_state):
        self.selectors_dict['annualised'] = checked_state

        self.plot_ts()

    def changed_peg_usdc(self, checked_state):
        self.selectors_dict['peg_usdc'] = checked_state

        self.plot_ts()

class Ui_MainWindow_Dev(object):
    #core_income_fund = DebankPortfolioTimeSeries()
    core_income_fund = PortfolioTimeSeries()

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 720)
        MainWindow.setMinimumSize(QSize(940, 560))
        self.styleSheet = QWidget(MainWindow)
        self.styleSheet.setObjectName(u"styleSheet")
        self.font = QFont()
        self.font.setFamily(u"Segoe UI")
        self.font.setPointSize(10)
        self.font.setBold(False)
        self.font.setItalic(False)
        self.styleSheet.setFont(self.font)
        self.styleSheet.setStyleSheet(
            u"/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "\n"
            "SET APP STYLESHEET - FULL STYLES HERE\n"
            "DARK THEME - DRACULA COLOR BASED\n"
            "\n"
            "///////////////////////////////////////////////////////////////////////////////////////////////// */\n"
            "\n"
            "QWidget{\n"
            "	color: rgb(221, 221, 221);\n"
            "	font: 10pt \"Segoe UI\";\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "Tooltip */\n"
            "QToolTip {\n"
            "	color: #ffffff;\n"
            "	background-color: rgba(33, 37, 43, 180);\n"
            "	border: 1px solid rgb(44, 49, 58);\n"
            "	background-image: none;\n"
            "	background-position: left center;\n"
            "    background-repeat: no-repeat;\n"
            "	border: none;\n"
            "	border-left: 2px solid rgb(0, 206, 124);\n"
            "	text-align: left;\n"
            "	padding-left: 8px;\n"
            "	margin: 0px;\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "Bg App */\n"
            "#bgApp {	\n"
            "	background"
            "-color: rgb(40, 44, 52);\n"
            "	border: 1px solid rgb(44, 49, 58);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "Left Menu */\n"
            "#leftMenuBg {	\n"
            "	background-color: rgb(33, 37, 43);\n"
            "}\n"
            "#topLogo {\n"
            "	background-color: rgb(33, 37, 43);\n"
            "	background-image: url(./images/images/osd_40.png);\n"
            "	background-position: centered;\n"
            "	background-repeat: no-repeat;\n"
            "}\n"
            "#titleLeftApp { font: 63 12pt \"Segoe UI Semibold\"; }\n"
            "#titleLeftDescription { font: 8pt \"Segoe UI\"; color: rgb(0, 206, 124); }\n"
            "\n"
            "/* MENUS */\n"
            "#topMenu .QPushButton {	\n"
            "	background-position: left center;\n"
            "    background-repeat: no-repeat;\n"
            "	border: none;\n"
            "	border-left: 22px solid transparent;\n"
            "	background-color: transparent;\n"
            "	text-align: left;\n"
            "	padding-left: 44px;\n"
            "}\n"
            "#topMenu .QPushButton:hover {\n"
            "	background-color: rgb(40, 44, 52);\n"
            "}\n"
            "#topMenu .QPushButton:pressed {	\n"
            "	background-color: rgb(0, 206, 124);\n"
            "	color: rgb(255, 255, 255);\n"
            "}\n"
            "#bottomMenu .QPushButton {	\n"
            "	background-position: left center;\n"
            "    background-repeat: no-repeat;\n"
            "	border: none;\n"
            "	border-left: 20px solid transparent;\n"
            "	background-color:transparent;\n"
            "	text-align: left;\n"
            "	padding-left: 44px;\n"
            "}\n"
            "#bottomMenu .QPushButton:hover {\n"
            "	background-color: rgb(40, 44, 52);\n"
            "}\n"
            "#bottomMenu .QPushButton:pressed {	\n"
            "	background-color: rgb(0, 206, 124);\n"
            "	color: rgb(255, 255, 255);\n"
            "}\n"
            "#leftMenuFrame{\n"
            "	border-top: 3px solid rgb(44, 49, 58);\n"
            "}\n"
            "\n"
            "/* Toggle Button */\n"
            "#toggleButton {\n"
            "	background-position: left center;\n"
            "    background-repeat: no-repeat;\n"
            "	border: none;\n"
            "	border-left: 20px solid transparent;\n"
            "	background-color: rgb(37, 41, 48);\n"
            "	text-align: left;\n"
            "	padding-left: 44px;\n"
            "	color: rgb(113, 126, 149);\n"
            "}\n"
            "#toggleButton:hover {\n"
            "	background-color: rgb(40, 44, 52);\n"
            "}\n"
            "#toggleButton:pressed {\n"
            "	background-color: rgb("
            "0, 206, 124);\n"
            "}\n"
            "\n"
            "/* Title Menu */\n"
            "#titleRightInfo { padding-left: 10px; }\n"
            "\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "Extra Tab */\n"
            "#extraLeftBox {	\n"
            "	background-color: rgb(44, 49, 58);\n"
            "}\n"
            "#extraTopBg{	\n"
            "	background-color: rgb(0, 206, 124)\n"
            "}\n"
            "\n"
            "/* Icon */\n"
            "#extraIcon {\n"
            "	background-position: center;\n"
            "	background-repeat: no-repeat;\n"
            "	background-image: url(:/icons/images/icons/icon_settings.png);\n"
            "}\n"
            "\n"
            "/* Label */\n"
            "#extraLabel { color: rgb(255, 255, 255); }\n"
            "\n"
            "/* Btn Close */\n"
            "#extraCloseColumnBtn { background-color: rgba(255, 255, 255, 0); border: none;  border-radius: 5px; }\n"
            "#extraCloseColumnBtn:hover { background-color: rgb(0, 206, 124); border-style: solid; border-radius: 4px; }\n"
            "#extraCloseColumnBtn:pressed { background-color: rgb(0, 206, 124); border-style: solid; border-radius: 4px; }\n"
            "\n"
            "/* Extra Content */\n"
            "#extraContent{\n"
            "	border"
            "-top: 3px solid rgb(40, 44, 52);\n"
            "}\n"
            "\n"
            "/* Extra Top Menus */\n"
            "#extraTopMenu .QPushButton {\n"
            "background-position: left center;\n"
            "    background-repeat: no-repeat;\n"
            "	border: none;\n"
            "	border-left: 22px solid transparent;\n"
            "	background-color:transparent;\n"
            "	text-align: left;\n"
            "	padding-left: 44px;\n"
            "}\n"
            "#extraTopMenu .QPushButton:hover {\n"
            "	background-color: rgb(40, 44, 52);\n"
            "}\n"
            "#extraTopMenu .QPushButton:pressed {	\n"
            "	background-color: rgb(0, 206, 124);\n"
            "	color: rgb(255, 255, 255);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "Content App */\n"
            "#contentTopBg{	\n"
            "	background-color: rgb(33, 37, 43);\n"
            "}\n"
            "#contentBottom{\n"
            "	border-top: 3px solid rgb(44, 49, 58);\n"
            "}\n"
            "\n"
            "/* Top Buttons */\n"
            "#rightButtons .QPushButton { background-color: rgba(255, 255, 255, 0); border: none;  border-radius: 5px; }\n"
            "#rightButtons .QPushButton:hover { background-color: rgb(44, 49, 57); border-sty"
            "le: solid; border-radius: 4px; }\n"
            "#rightButtons .QPushButton:pressed { background-color: rgb(23, 26, 30); border-style: solid; border-radius: 4px; }\n"
            "\n"
            "/* Theme Settings */\n"
            "#extraRightBox { background-color: rgb(44, 49, 58); }\n"
            "#themeSettingsTopDetail { background-color: rgb(0, 206, 124); }\n"
            "\n"
            "/* Bottom Bar */\n"
            "#bottomBar { background-color: rgb(44, 49, 58); }\n"
            "#bottomBar QLabel { font-size: 11px; color: rgb(113, 126, 149); padding-left: 10px; padding-right: 10px; padding-bottom: 2px; }\n"
            "\n"
            "/* CONTENT SETTINGS */\n"
            "/* MENUS */\n"
            "#contentSettings .QPushButton {	\n"
            "	background-position: left center;\n"
            "    background-repeat: no-repeat;\n"
            "	border: none;\n"
            "	border-left: 22px solid transparent;\n"
            "	background-color:transparent;\n"
            "	text-align: left;\n"
            "	padding-left: 44px;\n"
            "}\n"
            "#contentSettings .QPushButton:hover {\n"
            "	background-color: rgb(40, 44, 52);\n"
            "}\n"
            "#contentSettings .QPushButton:pressed {	\n"
            "	background-color: rgb(0, 206, 124);\n"
            "	color: rgb"
            "(255, 255, 255);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "QTableWidget */\n"
            "QTableWidget {	\n"
            #"	background-color: transparent;\n"
            "	padding: 10px;\n"
            "	border-radius: 5px;\n"
            "	gridline-color: rgb(44, 49, 58);\n"
            "	border-bottom: 1px solid rgb(44, 49, 60);\n"
            "}\n"
            "QTableWidget::item{\n"
            "	border-color: rgb(44, 49, 60);\n"
            "	padding-left: 5px;\n"
            "	padding-right: 5px;\n"
            "	gridline-color: rgb(44, 49, 60);\n"
            "}\n"
            "QTableWidget::item:selected{\n"
            "	background-color: rgb(0, 206, 124);\n"
            "}\n"
            "QHeaderView::section{\n"
            "	background-color: rgb(33, 37, 43);\n"
            "	max-width: 30px;\n"
            "	border: 1px solid rgb(44, 49, 58);\n"
            "	border-style: none;\n"
            "    border-bottom: 1px solid rgb(44, 49, 60);\n"
            "    border-right: 1px solid rgb(44, 49, 60);\n"
            "}\n"
            "QTableWidget::horizontalHeader {	\n"
            "	background-color: rgb(33, 37, 43);\n"
            "}\n"
            "QHeaderView::section:horizontal\n"
            "{\n"
            "    border: 1px solid rgb(33, 37, 43);\n"
            "	background-co"
            "lor: rgb(33, 37, 43);\n"
            "	padding: 3px;\n"
            "	border-top-left-radius: 7px;\n"
            "    border-top-right-radius: 7px;\n"
            "}\n"
            "QHeaderView::section:vertical\n"
            "{\n"
            "    border: 1px solid rgb(44, 49, 60);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "QTableView */\n"
            "QTableView {	\n"
            #"	background-color: transparent;\n"
            "	padding: 10px;\n"
            "	border-radius: 5px;\n"
            "	gridline-color: rgb(44, 49, 58);\n"
            "	border-bottom: 1px solid rgb(44, 49, 60);\n"
            "}\n"
            "QTableView::item{\n"
            "	border-color: rgb(44, 49, 60);\n"
            "	padding-left: 5px;\n"
            "	padding-right: 5px;\n"
            "	gridline-color: rgb(44, 49, 60);\n"
            "}\n"
            "QTableView::item:selected{\n"
            "	background-color: rgb(0, 206, 124);\n"
            "}\n"
            "QHeaderView::section{\n"
            "	background-color: rgb(33, 37, 43);\n"
            "	max-width: 30px;\n"
            "	border: 1px solid rgb(44, 49, 58);\n"
            "	border-style: none;\n"
            "    border-bottom: 1px solid rgb(44, 49, 60);\n"
            "    border-right: 1px solid rgb(44, 49, 60);\n"
            "}\n"
            "QTableView::horizontalHeader {	\n"
            "	background-color: rgb(33, 37, 43);\n"
            "}\n"
            "QHeaderView::section:horizontal\n"
            "{\n"
            "    border: 1px solid rgb(33, 37, 43);\n"
            "	background-co"
            "lor: rgb(33, 37, 43);\n"
            "	padding: 3px;\n"
            "	border-top-left-radius: 7px;\n"
            "    border-top-right-radius: 7px;\n"
            "}\n"
            "QHeaderView::section:vertical\n"
            "{\n"
            "    border: 1px solid rgb(44, 49, 60);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "LineEdit */\n"
            "QLineEdit {\n"
            "	background-color: rgb(33, 37, 43);\n"
            "	border-radius: 5px;\n"
            "	border: 2px solid rgb(33, 37, 43);\n"
            "	padding-left: 10px;\n"
            "	selection-color: rgb(255, 255, 255);\n"
            "	selection-background-color: rgb(0, 206, 124);\n"
            "}\n"
            "QLineEdit:hover {\n"
            "	border: 2px solid rgb(64, 71, 88);\n"
            "}\n"
            "QLineEdit:focus {\n"
            "	border: 2px solid rgb(91, 101, 124);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "PlainTextEdit */\n"
            "QPlainTextEdit {\n"
            "	background-color: rgb(27, 29, 35);\n"
            "	border-radius: 5px;\n"
            "	padding: 10px;\n"
            "	selection-color: rgb(255, 255, 255);\n"
            "	selection-background-c"
            "olor: rgb(0, 206, 124);\n"
            "}\n"
            "QPlainTextEdit  QScrollBar:vertical {\n"
            "    width: 8px;\n"
            " }\n"
            "QPlainTextEdit  QScrollBar:horizontal {\n"
            "    height: 8px;\n"
            " }\n"
            "QPlainTextEdit:hover {\n"
            "	border: 2px solid rgb(64, 71, 88);\n"
            "}\n"
            "QPlainTextEdit:focus {\n"
            "	border: 2px solid rgb(91, 101, 124);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "ScrollBars */\n"
            "QScrollBar:horizontal {\n"
            "    border: none;\n"
            "    background: rgb(52, 59, 72);\n"
            "    height: 8px;\n"
            "    margin: 0px 21px 0 21px;\n"
            "	border-radius: 0px;\n"
            "}\n"
            "QScrollBar::handle:horizontal {\n"
            "    background: rgb(0, 206, 124);\n"
            "    min-width: 25px;\n"
            "	border-radius: 4px\n"
            "}\n"
            "QScrollBar::add-line:horizontal {\n"
            "    border: none;\n"
            "    background: rgb(55, 63, 77);\n"
            "    width: 20px;\n"
            "	border-top-right-radius: 4px;\n"
            "    border-bottom-right-radius: 4px;\n"
            "    subcontrol-position: right;\n"
            "    subcontrol-origin: margin;\n"
            "}\n"
            ""
            "QScrollBar::sub-line:horizontal {\n"
            "    border: none;\n"
            "    background: rgb(55, 63, 77);\n"
            "    width: 20px;\n"
            "	border-top-left-radius: 4px;\n"
            "    border-bottom-left-radius: 4px;\n"
            "    subcontrol-position: left;\n"
            "    subcontrol-origin: margin;\n"
            "}\n"
            "QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal\n"
            "{\n"
            "     background: none;\n"
            "}\n"
            "QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal\n"
            "{\n"
            "     background: none;\n"
            "}\n"
            " QScrollBar:vertical {\n"
            "	border: none;\n"
            "    background: rgb(52, 59, 72);\n"
            "    width: 8px;\n"
            "    margin: 21px 0 21px 0;\n"
            "	border-radius: 0px;\n"
            " }\n"
            " QScrollBar::handle:vertical {	\n"
            "	background: rgb(0, 206, 124);\n"
            "    min-height: 25px;\n"
            "	border-radius: 4px\n"
            " }\n"
            " QScrollBar::add-line:vertical {\n"
            "     border: none;\n"
            "    background: rgb(55, 63, 77);\n"
            "     height: 20px;\n"
            "	border-bottom-left-radius: 4px;\n"
            "    border-bottom-right-radius: 4px;\n"
            "     subcontrol-position: bottom;\n"
            "     su"
            "bcontrol-origin: margin;\n"
            " }\n"
            " QScrollBar::sub-line:vertical {\n"
            "	border: none;\n"
            "    background: rgb(55, 63, 77);\n"
            "     height: 20px;\n"
            "	border-top-left-radius: 4px;\n"
            "    border-top-right-radius: 4px;\n"
            "     subcontrol-position: top;\n"
            "     subcontrol-origin: margin;\n"
            " }\n"
            " QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {\n"
            "     background: none;\n"
            " }\n"
            "\n"
            " QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n"
            "     background: none;\n"
            " }\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "CheckBox */\n"
            "QCheckBox::indicator {\n"
            "    border: 3px solid rgb(52, 59, 72);\n"
            "	width: 15px;\n"
            "	height: 15px;\n"
            "	border-radius: 10px;\n"
            "    background: rgb(44, 49, 60);\n"
            "}\n"
            "QCheckBox::indicator:hover {\n"
            "    border: 3px solid rgb(58, 66, 81);\n"
            "}\n"
            "QCheckBox::indicator:checked {\n"
            "    background: 3px solid rgb(52, 59, 72);\n"
            "	border: 3px solid rgb(52, 59, 72);	\n"
            "	back"
            "ground-image: url(:/icons/images/icons/cil-check-alt.png);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "RadioButton */\n"
            "QRadioButton::indicator {\n"
            "    border: 3px solid rgb(52, 59, 72);\n"
            "	width: 15px;\n"
            "	height: 15px;\n"
            "	border-radius: 10px;\n"
            "    background: rgb(44, 49, 60);\n"
            "}\n"
            "QRadioButton::indicator:hover {\n"
            "    border: 3px solid rgb(58, 66, 81);\n"
            "}\n"
            "QRadioButton::indicator:checked {\n"
            "    background: 3px solid rgb(94, 106, 130);\n"
            "	border: 3px solid rgb(52, 59, 72);	\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "ComboBox */\n"
            "QComboBox{\n"
            "	background-color: rgb(27, 29, 35);\n"
            "	border-radius: 5px;\n"
            "	border: 2px solid rgb(33, 37, 43);\n"
            "	padding: 5px;\n"
            "	padding-left: 10px;\n"
            "}\n"
            "QComboBox:hover{\n"
            "	border: 2px solid rgb(64, 71, 88);\n"
            "}\n"
            "QComboBox::drop-down {\n"
            "	subcontrol-origin: padding;\n"
            "	subco"
            "ntrol-position: top right;\n"
            "	width: 25px; \n"
            "	border-left-width: 3px;\n"
            "	border-left-color: rgba(39, 44, 54, 150);\n"
            "	border-left-style: solid;\n"
            "	border-top-right-radius: 3px;\n"
            "	border-bottom-right-radius: 3px;	\n"
            "	background-image: url(:/icons/images/icons/cil-arrow-bottom.png);\n"
            "	background-position: center;\n"
            "	background-repeat: no-reperat;\n"
            " }\n"
            "QComboBox QAbstractItemView {\n"
            "	color: rgb(0, 206, 124);	\n"
            "	background-color: rgb(33, 37, 43);\n"
            "	padding: 10px;\n"
            "	selection-background-color: rgb(39, 44, 54);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "Sliders */\n"
            "QSlider::groove:horizontal {\n"
            "    border-radius: 5px;\n"
            "    height: 10px;\n"
            "	margin: 0px;\n"
            "	background-color: rgb(52, 59, 72);\n"
            "}\n"
            "QSlider::groove:horizontal:hover {\n"
            "	background-color: rgb(55, 62, 76);\n"
            "}\n"
            "QSlider::handle:horizontal {\n"
            "    background-color: rgb(0, 206, 124);\n"
            "    border: none;\n"
            "    h"
            "eight: 10px;\n"
            "    width: 10px;\n"
            "    margin: 0px;\n"
            "	border-radius: 5px;\n"
            "}\n"
            "QSlider::handle:horizontal:hover {\n"
            "    background-color: rgb(195, 155, 255);\n"
            "}\n"
            "QSlider::handle:horizontal:pressed {\n"
            "    background-color: rgb(0, 206, 124);\n"
            "}\n"
            "\n"
            "QSlider::groove:vertical {\n"
            "    border-radius: 5px;\n"
            "    width: 10px;\n"
            "    margin: 0px;\n"
            "	background-color: rgb(52, 59, 72);\n"
            "}\n"
            "QSlider::groove:vertical:hover {\n"
            "	background-color: rgb(55, 62, 76);\n"
            "}\n"
            "QSlider::handle:vertical {\n"
            "    background-color: rgb(0, 206, 124);\n"
            "	border: none;\n"
            "    height: 10px;\n"
            "    width: 10px;\n"
            "    margin: 0px;\n"
            "	border-radius: 5px;\n"
            "}\n"
            "QSlider::handle:vertical:hover {\n"
            "    background-color: rgb(195, 155, 255);\n"
            "}\n"
            "QSlider::handle:vertical:pressed {\n"
            "    background-color: rgb(0, 206, 124);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "CommandLinkButton */\n"
            "QCommandLi"
            "nkButton {	\n"
            "	color: rgb(0, 206, 124);\n"
            "	border-radius: 5px;\n"
            "	padding: 5px;\n"
            "	color: rgb(0, 206, 124);\n"
            "}\n"
            "QCommandLinkButton:hover {	\n"
            "	color: rgb(0, 206, 124);\n"
            "	background-color: rgb(44, 49, 60);\n"
            "}\n"
            "QCommandLinkButton:pressed {	\n"
            "	color: rgb(0, 206, 124);\n"
            "	background-color: rgb(52, 58, 71);\n"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "DateEdit */\n"
            "QDateEdit{\n"
            "	background-color: rgb(27, 29, 35);\n"
            "	border-radius: 5px;\n"
            "	border: 2px solid rgb(33, 37, 43);\n"
            "	padding: 5px;\n"
            "	padding-left: 10px;\n"
            "}\n"
            "QDateEdit:hover{\n"
            "	border: 2px solid rgb(64, 71, 88);\n"
            "}\n"
            "QDateEdit::drop-down {\n"
            "	subcontrol-origin: padding;\n"
            "	subcontrol-position: top right;\n"
            "	width: 30px; \n"
            "	border-left-width: 3px;\n"
            "	border-left-color: rgba(39, 44, 54, 150);\n"
            "	border-left-style: solid;\n"
            "	border-top-right-radius: 3px;\n"
            "	border-bottom-right-radius: 3px;	\n"
            "	background-image: url(:/icons/images/icons/cil-arrow-bottom.png);\n"
            "	background-position: center;\n"
            "	background-repeat: no-repeat;\n"
            " }\n"
            #"QDateEdit QAbstractItemView {\n"
            #"	color: rgb(0, 206, 124);	\n"
            #"	background-color: rgb(33, 37, 43);\n"
            #"	padding: 10px;\n"
            #"	selection-background-color: rgb(39, 44, 54);\n"
            #"}\n"
            "QDateEdit::down-button:hover {\n"
            "   border: 2px solid rgb(64, 71, 88);"
            "\n"
            "QWidget#qt_calendar_navigationbar{\n"
            " background-color: rgb(27, 29, 35);"
            "}\n"
            "\n"
            "QWidget#calendar{\n"
            " background-color: rgb(27, 29, 35);"
            "}\n"
            "\n"
            "/* /////////////////////////////////////////////////////////////////////////////////////////////////\n"
            "Button */\n"
            "#pagesContainer QPushButton {\n"
            "	border: 2px solid rgb(52, 59, 72);\n"
            "	border-radius: 5px;	\n"
            "	background-color: rgb(52, 59, 72);\n"
            "}\n"
            "#pagesContainer QPushButton:hover {\n"
            "	background-color: rgb(57, 65, 80);\n"
            "	border: 2px solid rgb(61, 70, 86);\n"
            "}\n"
            "#pagesContainer QPushButton:pressed {	\n"
            "	background-color: rgb(35, 40, 49);\n"
            "	border: 2px solid rgb(43, 50, 61);\n"
            "}\n"
            "\n"
            "")
        self.appMargins = QVBoxLayout(self.styleSheet)
        self.appMargins.setSpacing(0)
        self.appMargins.setObjectName(u"appMargins")
        self.appMargins.setContentsMargins(10, 10, 10, 10)
        self.bgApp = QFrame(self.styleSheet)
        self.bgApp.setObjectName(u"bgApp")
        self.bgApp.setStyleSheet(u"")
        self.bgApp.setFrameShape(QFrame.NoFrame)
        self.bgApp.setFrameShadow(QFrame.Raised)
        self.appLayout = QHBoxLayout(self.bgApp)
        self.appLayout.setSpacing(0)
        self.appLayout.setObjectName(u"appLayout")
        self.appLayout.setContentsMargins(0, 0, 0, 0)
        self.leftMenuBg = QFrame(self.bgApp)
        self.leftMenuBg.setObjectName(u"leftMenuBg")
        self.leftMenuBg.setMinimumSize(QSize(60, 0))
        self.leftMenuBg.setMaximumSize(QSize(60, 16777215))
        self.leftMenuBg.setFrameShape(QFrame.NoFrame)
        self.leftMenuBg.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.leftMenuBg)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.topLogoInfo = QFrame(self.leftMenuBg)
        self.topLogoInfo.setObjectName(u"topLogoInfo")
        self.topLogoInfo.setMinimumSize(QSize(0, 50))
        self.topLogoInfo.setMaximumSize(QSize(16777215, 50))
        self.topLogoInfo.setFrameShape(QFrame.NoFrame)
        self.topLogoInfo.setFrameShadow(QFrame.Raised)
        self.topLogo = QFrame(self.topLogoInfo)
        self.topLogo.setObjectName(u"topLogo")
        self.topLogo.setGeometry(QRect(10, 5, 42, 42))
        self.topLogo.setMinimumSize(QSize(42, 42))
        self.topLogo.setMaximumSize(QSize(42, 42))
        self.topLogo.setFrameShape(QFrame.NoFrame)
        self.topLogo.setFrameShadow(QFrame.Raised)


        self.portfolio_selector_combo_2 = QComboBox(self.topLogoInfo)
        self.portfolio_selector_combo_2.addItem("DeFi Yield Fund")
        self.portfolio_selector_combo_2.addItem("Prime Fund")
        self.portfolio_selector_combo_2.addItem("Long/Short Fund")

        self.portfolio_selector_combo_2.setFont(self.font)
        self.portfolio_selector_combo_2.setAutoFillBackground(False)
        self.portfolio_selector_combo_2.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.portfolio_selector_combo_2.setIconSize(QSize(16, 16))
        self.portfolio_selector_combo_2.setFrame(True)
        # self.portfolio_selector_combo_2.setContentsMargins(10, 10, 10, 10)
        self.portfolio_selector_combo_2.setGeometry(QRect(70, 8, 160, 40))

        self.verticalLayout_3.addWidget(self.topLogoInfo)

        self.leftMenuFrame = QFrame(self.leftMenuBg)
        self.leftMenuFrame.setObjectName(u"leftMenuFrame")
        self.leftMenuFrame.setFrameShape(QFrame.NoFrame)
        self.leftMenuFrame.setFrameShadow(QFrame.Raised)
        self.verticalMenuLayout = QVBoxLayout(self.leftMenuFrame)
        self.verticalMenuLayout.setSpacing(0)
        self.verticalMenuLayout.setObjectName(u"verticalMenuLayout")
        self.verticalMenuLayout.setContentsMargins(0, 0, 0, 0)
        self.toggleBox = QFrame(self.leftMenuFrame)
        self.toggleBox.setObjectName(u"toggleBox")
        self.toggleBox.setMaximumSize(QSize(16777215, 45))
        self.toggleBox.setFrameShape(QFrame.NoFrame)
        self.toggleBox.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.toggleBox)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.toggleButton = QPushButton(self.toggleBox)
        self.toggleButton.setObjectName(u"toggleButton")
        self.sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.sizePolicy.setHorizontalStretch(0)
        self.sizePolicy.setVerticalStretch(0)
        self.sizePolicy.setHeightForWidth(self.toggleButton.sizePolicy().hasHeightForWidth())
        self.toggleButton.setSizePolicy(self.sizePolicy)
        self.toggleButton.setMinimumSize(QSize(0, 45))
        self.toggleButton.setFont(self.font)
        self.toggleButton.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggleButton.setLayoutDirection(Qt.LeftToRight)
        self.toggleButton.setStyleSheet(u"background-image: url(:/icons/images/icons/icon_menu.png);")

        self.verticalLayout_4.addWidget(self.toggleButton)

        self.verticalMenuLayout.addWidget(self.toggleBox)

        self.topMenu = QFrame(self.leftMenuFrame)
        self.topMenu.setObjectName(u"topMenu")
        self.topMenu.setFrameShape(QFrame.NoFrame)
        self.topMenu.setFrameShadow(QFrame.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.topMenu)
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)

        self.add_left_menu_buttons()

        self.verticalMenuLayout.addWidget(self.topMenu, 0, Qt.AlignTop)

        self.bottomMenu = QFrame(self.leftMenuFrame)
        self.bottomMenu.setObjectName(u"bottomMenu")
        self.bottomMenu.setFrameShape(QFrame.NoFrame)
        self.bottomMenu.setFrameShadow(QFrame.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.bottomMenu)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.toggleLeftBox = QPushButton(self.bottomMenu)
        self.toggleLeftBox.setObjectName(u"toggleLeftBox")
        self.sizePolicy.setHeightForWidth(self.toggleLeftBox.sizePolicy().hasHeightForWidth())
        self.toggleLeftBox.setSizePolicy(self.sizePolicy)
        self.toggleLeftBox.setMinimumSize(QSize(0, 45))
        self.toggleLeftBox.setFont(self.font)
        self.toggleLeftBox.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggleLeftBox.setLayoutDirection(Qt.LeftToRight)
        self.toggleLeftBox.setStyleSheet(u"background-image: url(:/icons/images/icons/icon_settings.png);")

        self.verticalLayout_9.addWidget(self.toggleLeftBox)

        self.verticalMenuLayout.addWidget(self.bottomMenu, 0, Qt.AlignBottom)

        self.verticalLayout_3.addWidget(self.leftMenuFrame)

        self.appLayout.addWidget(self.leftMenuBg)

        self.extraLeftBox = QFrame(self.bgApp)
        self.extraLeftBox.setObjectName(u"extraLeftBox")
        self.extraLeftBox.setMinimumSize(QSize(0, 0))
        self.extraLeftBox.setMaximumSize(QSize(0, 16777215))
        self.extraLeftBox.setFrameShape(QFrame.NoFrame)
        self.extraLeftBox.setFrameShadow(QFrame.Raised)
        self.extraColumLayout = QVBoxLayout(self.extraLeftBox)
        self.extraColumLayout.setSpacing(0)
        self.extraColumLayout.setObjectName(u"extraColumLayout")
        self.extraColumLayout.setContentsMargins(0, 0, 0, 0)
        self.extraTopBg = QFrame(self.extraLeftBox)
        self.extraTopBg.setObjectName(u"extraTopBg")
        self.extraTopBg.setMinimumSize(QSize(0, 50))
        self.extraTopBg.setMaximumSize(QSize(16777215, 50))
        self.extraTopBg.setFrameShape(QFrame.NoFrame)
        self.extraTopBg.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.extraTopBg)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.extraTopLayout = QGridLayout()
        self.extraTopLayout.setObjectName(u"extraTopLayout")
        self.extraTopLayout.setHorizontalSpacing(10)
        self.extraTopLayout.setVerticalSpacing(0)
        self.extraTopLayout.setContentsMargins(10, -1, 10, -1)
        self.extraIcon = QFrame(self.extraTopBg)
        self.extraIcon.setObjectName(u"extraIcon")
        self.extraIcon.setMinimumSize(QSize(20, 0))
        self.extraIcon.setMaximumSize(QSize(20, 20))
        self.extraIcon.setFrameShape(QFrame.NoFrame)
        self.extraIcon.setFrameShadow(QFrame.Raised)

        self.extraTopLayout.addWidget(self.extraIcon, 0, 0, 1, 1)

        self.extraLabel = QLabel(self.extraTopBg)
        self.extraLabel.setObjectName(u"extraLabel")
        self.extraLabel.setMinimumSize(QSize(150, 0))

        self.extraTopLayout.addWidget(self.extraLabel, 0, 1, 1, 1)

        self.extraCloseColumnBtn = QPushButton(self.extraTopBg)
        self.extraCloseColumnBtn.setObjectName(u"extraCloseColumnBtn")
        self.extraCloseColumnBtn.setMinimumSize(QSize(28, 28))
        self.extraCloseColumnBtn.setMaximumSize(QSize(28, 28))
        self.extraCloseColumnBtn.setCursor(QCursor(Qt.PointingHandCursor))
        icon = QIcon()
        icon.addFile(u":/icons/images/icons/icon_close.png", QSize(), QIcon.Normal, QIcon.Off)
        self.extraCloseColumnBtn.setIcon(icon)
        self.extraCloseColumnBtn.setIconSize(QSize(20, 20))

        self.extraTopLayout.addWidget(self.extraCloseColumnBtn, 0, 2, 1, 1)

        self.verticalLayout_5.addLayout(self.extraTopLayout)

        self.extraColumLayout.addWidget(self.extraTopBg)

        self.extraContent = QFrame(self.extraLeftBox)
        self.extraContent.setObjectName(u"extraContent")
        self.extraContent.setFrameShape(QFrame.NoFrame)
        self.extraContent.setFrameShadow(QFrame.Raised)
        self.verticalLayout_12 = QVBoxLayout(self.extraContent)
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.extraTopMenu = QFrame(self.extraContent)
        self.extraTopMenu.setObjectName(u"extraTopMenu")
        self.extraTopMenu.setFrameShape(QFrame.NoFrame)
        self.extraTopMenu.setFrameShadow(QFrame.Raised)
        self.verticalLayout_11 = QVBoxLayout(self.extraTopMenu)
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.btn_share = QPushButton(self.extraTopMenu)
        self.btn_share.setObjectName(u"btn_share")
        self.sizePolicy.setHeightForWidth(self.btn_share.sizePolicy().hasHeightForWidth())
        self.btn_share.setSizePolicy(self.sizePolicy)
        self.btn_share.setMinimumSize(QSize(0, 45))
        self.btn_share.setFont(self.font)
        self.btn_share.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_share.setLayoutDirection(Qt.LeftToRight)
        self.btn_share.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-share-boxed.png);")

        self.verticalLayout_11.addWidget(self.btn_share)

        self.btn_adjustments = QPushButton(self.extraTopMenu)
        self.btn_adjustments.setObjectName(u"btn_adjustments")
        self.sizePolicy.setHeightForWidth(self.btn_adjustments.sizePolicy().hasHeightForWidth())
        self.btn_adjustments.setSizePolicy(self.sizePolicy)
        self.btn_adjustments.setMinimumSize(QSize(0, 45))
        self.btn_adjustments.setFont(self.font)
        self.btn_adjustments.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_adjustments.setLayoutDirection(Qt.LeftToRight)
        self.btn_adjustments.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-equalizer.png);")

        self.verticalLayout_11.addWidget(self.btn_adjustments)

        self.btn_more = QPushButton(self.extraTopMenu)
        self.btn_more.setObjectName(u"btn_more")
        self.sizePolicy.setHeightForWidth(self.btn_more.sizePolicy().hasHeightForWidth())
        self.btn_more.setSizePolicy(self.sizePolicy)
        self.btn_more.setMinimumSize(QSize(0, 45))
        self.btn_more.setFont(self.font)
        self.btn_more.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_more.setLayoutDirection(Qt.LeftToRight)
        self.btn_more.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-layers.png);")

        self.verticalLayout_11.addWidget(self.btn_more)

        self.verticalLayout_12.addWidget(self.extraTopMenu, 0, Qt.AlignTop)

        self.extraCenter = QFrame(self.extraContent)
        self.extraCenter.setObjectName(u"extraCenter")
        self.extraCenter.setFrameShape(QFrame.NoFrame)
        self.extraCenter.setFrameShadow(QFrame.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.extraCenter)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.textEdit = QTextEdit(self.extraCenter)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setMinimumSize(QSize(222, 0))
        self.textEdit.setStyleSheet(u"background: transparent;")
        self.textEdit.setFrameShape(QFrame.NoFrame)
        self.textEdit.setReadOnly(True)

        self.verticalLayout_10.addWidget(self.textEdit)

        self.verticalLayout_12.addWidget(self.extraCenter)

        self.extraBottom = QFrame(self.extraContent)
        self.extraBottom.setObjectName(u"extraBottom")
        self.extraBottom.setFrameShape(QFrame.NoFrame)
        self.extraBottom.setFrameShadow(QFrame.Raised)

        self.verticalLayout_12.addWidget(self.extraBottom)

        self.extraColumLayout.addWidget(self.extraContent)

        self.appLayout.addWidget(self.extraLeftBox)

        self.contentBox = QFrame(self.bgApp)
        self.contentBox.setObjectName(u"contentBox")
        self.contentBox.setFrameShape(QFrame.NoFrame)
        self.contentBox.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.contentBox)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.contentTopBg = QFrame(self.contentBox)
        self.contentTopBg.setObjectName(u"contentTopBg")
        self.contentTopBg.setMinimumSize(QSize(0, 50))
        self.contentTopBg.setMaximumSize(QSize(16777215, 50))
        self.contentTopBg.setFrameShape(QFrame.NoFrame)
        self.contentTopBg.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.contentTopBg)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 10, 0)
        self.leftBox = QFrame(self.contentTopBg)
        self.leftBox.setObjectName(u"leftBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.leftBox.sizePolicy().hasHeightForWidth())
        self.leftBox.setSizePolicy(sizePolicy1)
        self.leftBox.setFrameShape(QFrame.NoFrame)
        self.leftBox.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.leftBox)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.titleRightInfo = QLabel(self.leftBox)
        self.titleRightInfo.setObjectName(u"titleRightInfo")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.titleRightInfo.sizePolicy().hasHeightForWidth())
        self.titleRightInfo.setSizePolicy(sizePolicy2)
        self.titleRightInfo.setMaximumSize(QSize(16777215, 45))
        self.titleRightInfo.setFont(self.font)
        self.titleRightInfo.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.titleRightInfo)

        self.horizontalLayout.addWidget(self.leftBox)

        self.rightButtons = QFrame(self.contentTopBg)
        self.rightButtons.setObjectName(u"rightButtons")
        self.rightButtons.setMinimumSize(QSize(0, 28))
        self.rightButtons.setFrameShape(QFrame.NoFrame)
        self.rightButtons.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.rightButtons)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.settingsTopBtn = QPushButton(self.rightButtons)
        self.settingsTopBtn.setObjectName(u"settingsTopBtn")
        self.settingsTopBtn.setMinimumSize(QSize(28, 28))
        self.settingsTopBtn.setMaximumSize(QSize(28, 28))
        self.settingsTopBtn.setCursor(QCursor(Qt.PointingHandCursor))
        icon1 = QIcon()
        icon1.addFile(u":/icons/images/icons/icon_settings.png", QSize(), QIcon.Normal, QIcon.Off)
        self.settingsTopBtn.setIcon(icon1)
        self.settingsTopBtn.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.settingsTopBtn)

        self.minimizeAppBtn = QPushButton(self.rightButtons)
        self.minimizeAppBtn.setObjectName(u"minimizeAppBtn")
        self.minimizeAppBtn.setMinimumSize(QSize(28, 28))
        self.minimizeAppBtn.setMaximumSize(QSize(28, 28))
        self.minimizeAppBtn.setCursor(QCursor(Qt.PointingHandCursor))
        icon2 = QIcon()
        icon2.addFile(u":/icons/images/icons/icon_minimize.png", QSize(), QIcon.Normal, QIcon.Off)
        self.minimizeAppBtn.setIcon(icon2)
        self.minimizeAppBtn.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.minimizeAppBtn)

        self.maximizeRestoreAppBtn = QPushButton(self.rightButtons)
        self.maximizeRestoreAppBtn.setObjectName(u"maximizeRestoreAppBtn")
        self.maximizeRestoreAppBtn.setMinimumSize(QSize(28, 28))
        self.maximizeRestoreAppBtn.setMaximumSize(QSize(28, 28))
        font3 = QFont()
        font3.setFamily(u"Segoe UI")
        font3.setPointSize(10)
        font3.setBold(False)
        font3.setItalic(False)
        font3.setStyleStrategy(QFont.PreferDefault)
        self.maximizeRestoreAppBtn.setFont(font3)
        self.maximizeRestoreAppBtn.setCursor(QCursor(Qt.PointingHandCursor))
        icon3 = QIcon()
        icon3.addFile(u":/icons/images/icons/icon_maximize.png", QSize(), QIcon.Normal, QIcon.Off)
        self.maximizeRestoreAppBtn.setIcon(icon3)
        self.maximizeRestoreAppBtn.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.maximizeRestoreAppBtn)

        self.closeAppBtn = QPushButton(self.rightButtons)
        self.closeAppBtn.setObjectName(u"closeAppBtn")
        self.closeAppBtn.setMinimumSize(QSize(28, 28))
        self.closeAppBtn.setMaximumSize(QSize(28, 28))
        self.closeAppBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.closeAppBtn.setIcon(icon)
        self.closeAppBtn.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.closeAppBtn)

        self.horizontalLayout.addWidget(self.rightButtons, 0, Qt.AlignRight)

        self.verticalLayout_2.addWidget(self.contentTopBg)

        self.contentBottom = QFrame(self.contentBox)
        self.contentBottom.setObjectName(u"contentBottom")
        self.contentBottom.setFrameShape(QFrame.NoFrame)
        self.contentBottom.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.contentBottom)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.content = QFrame(self.contentBottom)
        self.content.setObjectName(u"content")
        self.content.setFrameShape(QFrame.NoFrame)
        self.content.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.content)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.pagesContainer = QFrame(self.content)
        self.pagesContainer.setObjectName(u"pagesContainer")
        self.pagesContainer.setStyleSheet(u"")
        self.pagesContainer.setFrameShape(QFrame.NoFrame)
        self.pagesContainer.setFrameShadow(QFrame.Raised)
        self.verticalLayout_15 = QVBoxLayout(self.pagesContainer)
        self.verticalLayout_15.setSpacing(0)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(10, 10, 10, 10)
        self.stackedWidget = QStackedWidget(self.pagesContainer)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setStyleSheet(u"background: transparent;")

        self.create_modules_widgets()

        self.verticalLayout_15.addWidget(self.stackedWidget)

        self.horizontalLayout_4.addWidget(self.pagesContainer)
        '''
        self.extraRightBox = QFrame(self.content)
        self.extraRightBox.setObjectName(u"extraRightBox")
        self.extraRightBox.setMinimumSize(QSize(0, 0))
        self.extraRightBox.setMaximumSize(QSize(0, 16777215))
        self.extraRightBox.setFrameShape(QFrame.NoFrame)
        self.extraRightBox.setFrameShadow(QFrame.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.extraRightBox)
        self.verticalLayout_7.setSpacing(0)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.themeSettingsTopDetail = QFrame(self.extraRightBox)
        self.themeSettingsTopDetail.setObjectName(u"themeSettingsTopDetail")
        self.themeSettingsTopDetail.setMaximumSize(QSize(16777215, 3))
        self.themeSettingsTopDetail.setFrameShape(QFrame.NoFrame)
        self.themeSettingsTopDetail.setFrameShadow(QFrame.Raised)

        self.verticalLayout_7.addWidget(self.themeSettingsTopDetail)

        self.contentSettings = QFrame(self.extraRightBox)
        self.contentSettings.setObjectName(u"contentSettings")
        self.contentSettings.setFrameShape(QFrame.NoFrame)
        self.contentSettings.setFrameShadow(QFrame.Raised)
        self.verticalLayout_13 = QVBoxLayout(self.contentSettings)
        self.verticalLayout_13.setSpacing(0)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.topMenus = QFrame(self.contentSettings)
        self.topMenus.setObjectName(u"topMenus")
        self.topMenus.setFrameShape(QFrame.NoFrame)
        self.topMenus.setFrameShadow(QFrame.Raised)
        self.verticalLayout_14 = QVBoxLayout(self.topMenus)
        self.verticalLayout_14.setSpacing(0)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(0, 0, 0, 0)
        self.btn_message = QPushButton(self.topMenus)
        self.btn_message.setObjectName(u"btn_message")
        self.sizePolicy.setHeightForWidth(self.btn_message.sizePolicy().hasHeightForWidth())
        self.btn_message.setSizePolicy(self.sizePolicy)
        self.btn_message.setMinimumSize(QSize(0, 45))
        self.btn_message.setFont(self.font)
        self.btn_message.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_message.setLayoutDirection(Qt.LeftToRight)
        self.btn_message.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-envelope-open.png);")

        self.verticalLayout_14.addWidget(self.btn_message)

        self.btn_print = QPushButton(self.topMenus)
        self.btn_print.setObjectName(u"btn_print")
        self.sizePolicy.setHeightForWidth(self.btn_print.sizePolicy().hasHeightForWidth())
        self.btn_print.setSizePolicy(self.sizePolicy)
        self.btn_print.setMinimumSize(QSize(0, 45))
        self.btn_print.setFont(self.font)
        self.btn_print.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_print.setLayoutDirection(Qt.LeftToRight)
        self.btn_print.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-print.png);")

        self.verticalLayout_14.addWidget(self.btn_print)

        self.btn_logout = QPushButton(self.topMenus)
        self.btn_logout.setObjectName(u"btn_logout")
        self.sizePolicy.setHeightForWidth(self.btn_logout.sizePolicy().hasHeightForWidth())
        self.btn_logout.setSizePolicy(self.sizePolicy)
        self.btn_logout.setMinimumSize(QSize(0, 45))
        self.btn_logout.setFont(self.font)
        self.btn_logout.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_logout.setLayoutDirection(Qt.LeftToRight)
        self.btn_logout.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-account-logout.png);")

        self.verticalLayout_14.addWidget(self.btn_logout)

        self.verticalLayout_13.addWidget(self.topMenus, 0, Qt.AlignTop)

        self.verticalLayout_7.addWidget(self.contentSettings)

        self.horizontalLayout_4.addWidget(self.extraRightBox)
        '''
        self.verticalLayout_6.addWidget(self.content)

        self.bottomBar = QFrame(self.contentBottom)
        self.bottomBar.setObjectName(u"bottomBar")
        self.bottomBar.setMinimumSize(QSize(0, 22))
        self.bottomBar.setMaximumSize(QSize(16777215, 22))
        self.bottomBar.setFrameShape(QFrame.NoFrame)
        self.bottomBar.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.bottomBar)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.creditsLabel = QLabel(self.bottomBar)
        self.creditsLabel.setObjectName(u"creditsLabel")
        self.creditsLabel.setMaximumSize(QSize(16777215, 16))
        font5 = QFont()
        font5.setFamily(u"Segoe UI")
        font5.setBold(False)
        font5.setItalic(False)
        self.creditsLabel.setFont(font5)
        self.creditsLabel.setAlignment(Qt.AlignLeading | Qt.AlignLeft | Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.creditsLabel)

        self.version = QLabel(self.bottomBar)
        self.version.setObjectName(u"version")
        self.version.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.version)

        self.frame_size_grip = QFrame(self.bottomBar)
        self.frame_size_grip.setObjectName(u"frame_size_grip")
        self.frame_size_grip.setMinimumSize(QSize(20, 0))
        self.frame_size_grip.setMaximumSize(QSize(20, 16777215))
        self.frame_size_grip.setFrameShape(QFrame.NoFrame)
        self.frame_size_grip.setFrameShadow(QFrame.Raised)

        self.horizontalLayout_5.addWidget(self.frame_size_grip)

        self.verticalLayout_6.addWidget(self.bottomBar)

        self.verticalLayout_2.addWidget(self.contentBottom)

        self.appLayout.addWidget(self.contentBox)

        self.appMargins.addWidget(self.bgApp)

        MainWindow.setCentralWidget(self.styleSheet)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(2)

        QMetaObject.connectSlotsByName(MainWindow)

        #MainWindow.showMaximized()

    def add_left_menu_buttons(self):
        self.btn_home = self.initialise_left_menu_button(button_name=u"home")
        self.btn_home.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-home.png);")
        self.verticalLayout_8.addWidget(self.btn_home)

        self.btn_portfolio = self.initialise_left_menu_button(button_name=u"btn_portfolio")
        self.btn_portfolio.setStyleSheet(
            u"background-image: url(:/icons/images/icons/cil-gamepad.png);")  # TODO change icon
        self.verticalLayout_8.addWidget(self.btn_portfolio)

        self.btn_performance = self.initialise_left_menu_button(button_name=u"btn_performance")
        self.btn_performance.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-file.png);")
        self.verticalLayout_8.addWidget(self.btn_performance)

        self.btn_risk = self.initialise_left_menu_button(button_name=u"btn_risk")
        self.btn_risk.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-save.png)")
        self.verticalLayout_8.addWidget(self.btn_risk)

        self.btn_optim = self.initialise_left_menu_button(button_name=u"btn_optim")
        self.btn_optim.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-x.png);")
        self.verticalLayout_8.addWidget(self.btn_optim)

        self.btn_qualitative = self.initialise_left_menu_button(button_name=u"btn_qualitative")
        self.btn_qualitative.setStyleSheet(u"background-image: url(:/icons/images/icons/cil-x.png);")
        self.verticalLayout_8.addWidget(self.btn_qualitative)

    def initialise_left_menu_button(self, button_name):
        button = QPushButton(self.topMenu)

        button.setObjectName(button_name)
        self.sizePolicy.setHeightForWidth(button.sizePolicy().hasHeightForWidth())
        button.setSizePolicy(self.sizePolicy)
        button.setMinimumSize(QSize(0, 45))
        button.setFont(self.font)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setLayoutDirection(Qt.LeftToRight)

        return button

    def create_modules_widgets(self):
        self.create_home_module()
        self.create_portfolio_module()
        self.create_performance_module()
        self.create_optim_module()

    def create_home_module(self):
        self.home = QWidget()
        self.home.setObjectName(u"home")
        self.home.setStyleSheet(u"background-image: url(./images/images/OSD.png);\n"
                                "background-position: center;\n"
                                "background-repeat: no-repeat;")

        self.home_vertical_layout = QVBoxLayout(self.home)
        self.home_vertical_layout.setAlignment(Qt.AlignCenter)
        self.home_vertical_layout.setSpacing(10)
        self.home_vertical_layout.setObjectName(u"home_vertical_layout")
        self.home_vertical_layout.setContentsMargins(10, 10, 10, 10)

        '''label_for_image = QLabel(self.home)
        pixmap = QPixmap("./images/images/osd.png")
        label_for_image.setPixmap(pixmap)'''

        # self.home_vertical_layout.addWidget(label_for_image, 0)#, QtCore.Qt.AlignCenter)
        self.stackedWidget.addWidget(self.home)

    def create_portfolio_module(self):
        self.portfolio = QWidget()
        self.portfolio.setObjectName(u"portfolio")
        '''self.portfolio.setStyleSheet(u"background-image: url(./images/images/osd.png);\n"
                                     "background-position: center;\n"
                                     "background-repeat: no-repeat;")'''
        self.portfolio_vertical_layout = QVBoxLayout(self.portfolio)
        self.portfolio_vertical_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        #self.portfolio_top_selectors = QWidget(self.portfolio)
        self.portfolio_top_selectors_layout = QHBoxLayout()
        self.portfolio_top_selectors_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.portfolio_vertical_layout.addLayout(self.portfolio_top_selectors_layout)

        self.portfolio_table_view = TableView(self.portfolio)
        self.portfolio_model = DefiPortfolioModel(self.core_income_fund)
        self.portfolio_table_view.setModel(self.portfolio_model)

        self.portfolio_vertical_layout.addWidget(self.portfolio_table_view, alignment=Qt.AlignHCenter | Qt.AlignTop)

        #Start of selectors creation

        self.portfolio_calendar_popup = CalendarSelectorWidget(start_date=QDate(2022, 10, 5))

        self.portfolio_calendar_popup.calendar.clicked.connect(self.portfolio_model.date_change)

        self.portfolio_top_selectors_layout.addWidget(self.portfolio_calendar_popup)

        self.portfolio_aggregation_level_text = QLabel("Aggregation Level: ")
        self.portfolio_top_selectors_layout.addWidget(self.portfolio_aggregation_level_text)

        self.portfolio_aggregation_level = QComboBox()
        self.portfolio_aggregation_level.addItem("Position")
        self.portfolio_aggregation_level.addItem("Pool")
        self.portfolio_aggregation_level.addItem("Dapp")
        self.portfolio_aggregation_level.addItem("Token")
        self.portfolio_aggregation_level.addItem("Chain")
        self.portfolio_aggregation_level.setFont(self.font)
        self.portfolio_aggregation_level.setAutoFillBackground(False)
        self.portfolio_aggregation_level.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.portfolio_aggregation_level.setIconSize(QSize(16, 16))
        self.portfolio_aggregation_level.setFrame(True)
        self.portfolio_aggregation_level.setGeometry(QRect(70, 8, 160, 40))

        self.portfolio_aggregation_level.currentTextChanged.connect(self.portfolio_model.aggregation_level_change)
        self.portfolio_top_selectors_layout.addWidget(self.portfolio_aggregation_level)
        #TODO Pool agg

        self.portfolio_price_source_text = QLabel("Price Source: ")
        self.portfolio_top_selectors_layout.addWidget(self.portfolio_price_source_text)

        self.portfolio_price_source = QComboBox()
        self.portfolio_price_source.addItem("DeBank")
        self.portfolio_price_source.addItem("On-chain")
        self.portfolio_price_source.addItem("Coingecko")
        self.portfolio_price_source.setFont(self.font)
        self.portfolio_price_source.setAutoFillBackground(False)
        self.portfolio_price_source.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.portfolio_price_source.setIconSize(QSize(16, 16))
        self.portfolio_price_source.setFrame(True)
        self.portfolio_price_source.setGeometry(QRect(70, 8, 160, 40))
        self.portfolio_top_selectors_layout.addWidget(self.portfolio_price_source)

        self.portfolio_peg_stables_text = QLabel("Peg Stables to $1: ")
        self.portfolio_top_selectors_layout.addWidget(self.portfolio_peg_stables_text)

        self.portfolio_peg_stables = QCheckBox()
        self.portfolio_top_selectors_layout.addWidget(self.portfolio_peg_stables)

        self.stackedWidget.addWidget(self.portfolio)

    def create_performance_module(self):
        self.performance = QWidget()
        self.performance.setObjectName(u"performance")
        '''self.performance.setStyleSheet(u"background-image: url(./images/images/osd.png);\n"
                                       "background-position: center;\n"
                                       "background-repeat: no-repeat;")'''

        self.performance_vertical_layout = QVBoxLayout(self.performance)
        #self.performance_vertical_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        #self.performance_vertical_layout.setSpacing(10)
        self.performance_vertical_layout.setObjectName(u"performance_vertical_layout")
        #self.performance_vertical_layout.setContentsMargins(10, 10, 10, 10)

        canvas = PerformanceGraphWidget(parent=self.performance, portfolio_ts=self.core_income_fund)

        self.performance_top_selector_layout = QHBoxLayout()
        self.performance_top_selector_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.performance_vertical_layout.addLayout(self.performance_top_selector_layout)

        self.performance_from_date_label = QLabel("From Date:")
        self.performance_from_date_box = CalendarSelectorWidget(start_date=QDate(2022, 10, 5))
        self.performance_from_date_box.calendar.clicked.connect(canvas.changed_from_date)

        self.performance_to_date_label = QLabel("To Date:")
        self.performance_to_date_box = CalendarSelectorWidget(start_date=QDate(2022, 10, 5))
        self.performance_to_date_box.calendar.clicked.connect(canvas.changed_to_date)

        self.performance_rolling_avg_label = QLabel("Rolling Average Days:")
        self.performance_rolling_avg_dropdown = QComboBox()
        self.performance_rolling_avg_dropdown.addItem("1")
        self.performance_rolling_avg_dropdown.addItem("3")
        self.performance_rolling_avg_dropdown.addItem("7")
        self.performance_rolling_avg_dropdown.addItem("30")
        self.performance_rolling_avg_dropdown.setFont(self.font)
        self.performance_rolling_avg_dropdown.setAutoFillBackground(False)
        self.performance_rolling_avg_dropdown.setStyleSheet(u"background-color: rgb(33, 37, 43);")
        self.performance_rolling_avg_dropdown.setIconSize(QSize(16, 16))
        self.performance_rolling_avg_dropdown.setFrame(True)
        self.performance_rolling_avg_dropdown.setGeometry(QRect(70, 8, 160, 40))

        self.performance_rolling_avg_dropdown.currentTextChanged.connect(canvas.changed_rolling_avg_window)

        self.performance_returns_label = QLabel("Returns:")
        self.performance_returns_checkbox = QCheckBox()
        self.performance_returns_checkbox.clicked.connect(canvas.changed_returns_checkbox)

        self.performance_annualise_label = QLabel("Annualise:")
        self.performance_annualise_checkbox = QCheckBox()
        self.performance_annualise_checkbox.clicked.connect(canvas.changed_annualised_checkbox)

        self.performance_peg_usdc_label = QLabel("Peg USDC to Par:")
        self.performance_peg_usdc_checkbox = QCheckBox()
        self.performance_peg_usdc_checkbox.clicked.connect(canvas.changed_peg_usdc)

        self.performance_top_selector_layout.addWidget(self.performance_from_date_label)
        self.performance_top_selector_layout.addWidget(self.performance_from_date_box)
        self.performance_top_selector_layout.addWidget(self.performance_to_date_label)
        self.performance_top_selector_layout.addWidget(self.performance_to_date_box)
        self.performance_top_selector_layout.addWidget(self.performance_rolling_avg_label)
        self.performance_top_selector_layout.addWidget(self.performance_rolling_avg_dropdown)
        self.performance_top_selector_layout.addWidget(self.performance_returns_label)
        self.performance_top_selector_layout.addWidget(self.performance_returns_checkbox)
        self.performance_top_selector_layout.addWidget(self.performance_annualise_label)
        self.performance_top_selector_layout.addWidget(self.performance_annualise_checkbox)
        self.performance_top_selector_layout.addWidget(self.performance_peg_usdc_label)
        self.performance_top_selector_layout.addWidget(self.performance_peg_usdc_checkbox)

        self.performance_vertical_layout.addWidget(canvas, stretch=1)

        self.stackedWidget.addWidget(self.performance)

    def create_optim_module(self):
        print("")


    '''
    def create_performance_attribution_module(self):
        self.performance_attribution = QWidget()
        self.performance_attribution.setObjectName('performance_attribution')

        self.performance_attribution_vertical_layout = QVBoxLayout(self.performance_attribution)
        self.performance_attribution_vertical_layout.setObjectName(u"performance_attribution_vertical_layout")

        self.performance_attribution_top_selector_layout = QHBoxLayout()
        self.performance_attribution_top_selector_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.performance_attribution_vertical_layout.addLayout(self.performance_attribution_top_selector_layout)

        self.performance_attribution_from_date_label = QLabel("From Date:")
        self.performance_attribution_from_date_box = CalendarSelectorWidget(start_date=QDate(2022, 10, 5))

        self.performance_attribution_to_date_label = QLabel("To Date:")
        self.performance_attribution_to_date_box = CalendarSelectorWidget(start_date=QDate(2022, 10, 5))

        self.performance_attribution_annualise_label = QLabel("Annualise:")
        self.performance_attribution_annualise_checkbox = QCheckBox()

        self.performance_attribution_top_selector_layout.addWidget(self.performance_attribution_from_date_label)
        self.performance_attribution_top_selector_layout.addWidget(self.performance_attribution_from_date_box)
        self.performance_attribution_top_selector_layout.addWidget(self.performance_attribution_to_date_label)
        self.performance_attribution_top_selector_layout.addWidget(self.performance_attribution_to_date_box)
        self.performance_attribution_top_selector_layout.addWidget(self.performance_attribution_annualise_label)
        self.performance_attribution_top_selector_layout.addWidget(self.performance_attribution_annualise_checkbox)

        self.stackedWidget.addWidget(self.performance_attribution)
    '''
    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        # self.titleLeftApp.setText(QCoreApplication.translate("MainWindow", u"Old Street Digital", None))
        # self.titleLeftDescription.setText(QCoreApplication.translate("MainWindow", u"Crypo Asset Management", None))
        self.toggleButton.setText(QCoreApplication.translate("MainWindow", u"Hide", None))
        self.btn_home.setText(QCoreApplication.translate("MainWindow", u"Home", None))
        self.btn_portfolio.setText(QCoreApplication.translate("MainWindow", u"Portfolio", None))
        self.btn_performance.setText(QCoreApplication.translate("MainWindow", u"Performance", None))
        self.btn_risk.setText(QCoreApplication.translate("MainWindow", u"Risk", None))
        self.btn_optim.setText(QCoreApplication.translate("MainWindow", u"Optim", None))
        self.btn_qualitative.setText(QCoreApplication.translate("MainWindow", u"Qualitative", None))
        self.toggleLeftBox.setText(QCoreApplication.translate("MainWindow", u"Left Box", None))
        self.extraLabel.setText(QCoreApplication.translate("MainWindow", u"Left Box", None))
        # if QT_CONFIG(tooltip)
        self.extraCloseColumnBtn.setToolTip(QCoreApplication.translate("MainWindow", u"Close left box", None))
        # endif // QT_CONFIG(tooltip)
        self.extraCloseColumnBtn.setText("")
        self.btn_share.setText(QCoreApplication.translate("MainWindow", u"Share", None))
        self.btn_adjustments.setText(QCoreApplication.translate("MainWindow", u"Adjustments", None))
        self.btn_more.setText(QCoreApplication.translate("MainWindow", u"More", None))
        self.textEdit.setHtml(QCoreApplication.translate("MainWindow",
                                                         u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                                         "<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
                                                         "p, li { white-space: pre-wrap; }\n"
                                                         "</style></head><body style=\" font-family:'Segoe UI'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
                                                         "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt; font-weight:600; color:#ff79c6;\">PyDracula</span></p>\n"
                                                         "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#ffffff;\">An interface created using Python and PySide (support for PyQt), and with colors based on the Dracula theme created by Zeno Rocha.</span></p>\n"
                                                         "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-inde"
                                                         "nt:0; text-indent:0px;\"><span style=\" color:#ffffff;\">MIT License</span></p>\n"
                                                         "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" color:#bd93f9;\">Created by: Wanderson M. Pimenta</span></p>\n"
                                                         "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt; font-weight:600; color:#ff79c6;\">Convert UI</span></p>\n"
                                                         "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; color:#ffffff;\">pyside6-uic main.ui &gt; ui_main.py</span></p>\n"
                                                         "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:12pt; font-weight:600; color:#ff79c6;\">Convert QRC</span></p>\n"
                                                         "<p align=\"center\" "
                                                         "style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:9pt; color:#ffffff;\">pyside6-rcc resources.qrc -o resources_rc.py</span></p></body></html>",
                                                         None))
        self.titleRightInfo.setText(
            QCoreApplication.translate("MainWindow", u"Old Street Digital Proprietary Asset Management Software", None))
        # if QT_CONFIG(tooltip)
        self.settingsTopBtn.setToolTip(QCoreApplication.translate("MainWindow", u"Settings", None))
        # endif // QT_CONFIG(tooltip)
        self.settingsTopBtn.setText("")
        # if QT_CONFIG(tooltip)
        self.minimizeAppBtn.setToolTip(QCoreApplication.translate("MainWindow", u"Minimize", None))
        # endif // QT_CONFIG(tooltip)
        self.minimizeAppBtn.setText("")
        # if QT_CONFIG(tooltip)
        self.maximizeRestoreAppBtn.setToolTip(QCoreApplication.translate("MainWindow", u"Maximize", None))
        # endif // QT_CONFIG(tooltip)
        self.maximizeRestoreAppBtn.setText("")
        # if QT_CONFIG(tooltip)
        self.closeAppBtn.setToolTip(QCoreApplication.translate("MainWindow", u"Close", None))
        # endif // QT_CONFIG(tooltip)
        self.closeAppBtn.setText("")

        # self.creditsLabel.setText(QCoreApplication.translate("MainWindow", u"By: Wanderson M. Pimenta", None))
        self.version.setText(QCoreApplication.translate("MainWindow", u"v1.0.0", None))
    # retranslateUi
