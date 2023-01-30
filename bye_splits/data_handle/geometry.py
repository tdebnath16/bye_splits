# coding: utf-8

_all_ = [ 'GeometryData' ]

import os
from pathlib import Path
import sys
parent_dir = os.path.abspath(__file__ + 2 * '/..')
sys.path.insert(0, parent_dir)

import numpy as np
import yaml
import awkward as ak
import uproot as up
import pandas as pd
import logging

from utils import params, common
from data_handle.base import BaseData

class GeometryData(BaseData):
    """
    Handles V11 HGCAL geometry.
    Uses the orientation #1 of bottom row of slide 4 in
    https://indico.cern.ch/event/1111846/contributions/4675223/attachments/2372915/4052852/PartialsRotation.pdf
    """
    def __init__(self, inname='', reprocess=False, logger=None):
        super().__init__(inname, 'geom', reprocess, logger)
        self.dataset = None
        self.dname = 'tc'
        with open(params.viz_kw['CfgDataPath'], 'r') as afile:
            cfg = yaml.safe_load(afile)
            self.var = common.dot_dict(cfg['varGeometry'])

        self.readvars = list(self.var.values())
        self.readvars.remove(self.var.wvs)
        self.readvars.remove(self.var.c)

        self.cu, self.cv = 'triggercellu', 'triggercellv'
        self.wu, self.wv = 'waferu', 'waferv'

        ## geometry-specific parameters
        self.waferWidth = cfg['geometry']['waferSize'] #this defines all other sizes
        self.sensorSeparation = cfg['geometry']['sensorSeparation']
        self.N = 4 #number of cells per wafer side
        self.c30 = np.sqrt(3)/2 #cossine of 30 degrees
        self.t30 = 1/np.sqrt(3) #tangent of 30 degrees
        self.R = self.waferWidth / (3 * self.N)
        self.r = self.R * self.c30
        self.cellDistX = self.waferWidth/8.
        self.cellDistY = self.cellDistX * self.t30

    def cell_location(self, df):
        """
        Filter TC location in wafer based on the orientation: up-right, up-left and bottom.
        In V11 "orientation 0" actually corresponds to 6, as the concept of orientation is only introduced for later versions.
        """
        conds = {'UL': ~(((df['waferorient']==6) & (df[self.cu] >= self.N) & (df[self.cu] > df[self.cv])) |
                         ((df['waferorient']<6) & (df[self.cv] < self.N) & (df[self.cu] > df[self.cv]))),

                 'UR': ~(((df['waferorient']==6) & (df[self.cv] >= self.N) & (df[self.cu] <= df[self.cv])) |
                         ((df['waferorient']<6) & (df[self.cv] >= self.N) & (df[self.cu] >= self.N))),

                 'B':  ~(((df['waferorient']==6) & (df[self.cu] < self.N) & (df[self.cv] < self.N)) |
                         ((df['waferorient']<6) & (df[self.cu] < self.N) & (df[self.cv] >= df[self.cu])))}
        df['cloc'] = np.nan
        df['cloc'] = df['cloc'].where(conds['B'], 'B')
        df['cloc'] = df['cloc'].where(conds['UL'], 'UL')
        df['cloc'] = df['cloc'].where(conds['UR'], 'UR')
        return df

    def cell_location_shift(self, df):
        """
        Shift the position of TCs according to their location to allow an aligned display.
        The true cell position becomes however more distant from the displayed cell center.
        """
        df.loc[:, 'tc_y'] = np.where(df['cloc']=='UR', df['tc_y']+self.cellDistY, df['tc_y'])
        df.loc[:, 'tc_x'] = np.where(df['cloc']=='B', df['tc_x']+self.cellDistX/2, df['tc_x'])
        df.loc[:, 'tc_y'] = np.where(df['cloc']=='B', df['tc_y']+self.cellDistY/2, df['tc_y'])
        return df

    def filter_columns(self, d):
        """Filter some columns to reduce memory usage"""
        cols_to_remove = ['color']
        cols = [x for x in d.fields if x not in cols_to_remove]
        return d[cols]

    def _from_parquet_to_geometry(self, ds, region):
        """
        Steps required for going from parquet format to full pandas geometry dataframe
        In principle all these steps could be done without using pandas,
        but the latter improves clarity.
        """
        print('check from 0')
        ds = ak.to_dataframe(ds)
        print('check from 1')
        ds = self.region_selection(ds, region)
        print('check from 2')
        ds = self.prepare_for_display(ds)
        print('check from 3')
        return ds

    def prepare_for_display(self, df, library='bokeh'):
        """Prepares dataframe to be displayed by certain libraries."""
        libraries = ('bokeh', )
        assert library in libraries
        
        df['wafer_shift_x'] = (-2*df[self.wu] + df[self.wv])*(self.waferWidth+self.sensorSeparation)/2
        df['wafer_shift_y'] = (self.c30*df[self.wv])*(self.waferWidth+self.sensorSeparation)
    
        # cells_conversion = (lambda cu,cv: (1.5*(cv-cu)+0.5) * self.R,
        #                     lambda cu,cv: (cv+cu-2*self.N+1) * self.r) #orientation 6
        cells_conversion = (lambda cu,cv: (1.5*(cv-self.N)+1) * self.R,
                            lambda cu,cv: (2*cu-cv-self.N) * self.r) #orientation 7

        univ_wcenterx = cells_conversion[0](3,3) + self.cellDistX
        univ_wcentery = cells_conversion[1](3,3) + 3*self.cellDistY/2
        scale_x, scale_y = self.waferWidth/2, self.waferWidth/(2*self.c30)
        
        xcorners, ycorners = ([] for _ in range(2))
        xcorners.append(univ_wcenterx - scale_x)
        xcorners.append(univ_wcenterx)
        xcorners.append(univ_wcenterx + scale_x)
        xcorners.append(univ_wcenterx + scale_x)
        xcorners.append(univ_wcenterx)
        xcorners.append(univ_wcenterx - scale_x)
        ysub = np.sqrt(scale_y*scale_y-scale_x*scale_x)
        ycorners.append(univ_wcentery - ysub)
        ycorners.append(univ_wcentery - scale_y)
        ycorners.append(univ_wcentery - ysub)
        ycorners.append(univ_wcentery + ysub)
        ycorners.append(univ_wcentery + scale_y)
        ycorners.append(univ_wcentery + ysub)
            
        xpoint, x0, x1, x2, x3 = ({} for _ in range(5))
        ypoint, y0, y1, y2, y3 = ({} for _ in range(5))
        xaxis, yaxis = ({} for _ in range(2))

        df['tc_x_center'] = cells_conversion[0](df[self.cu],df[self.cv])
        df['tc_y_center'] = cells_conversion[1](df[self.cu],df[self.cv])
        df['tc_x'] = df.wafer_shift_x + df['tc_x_center']
        df['tc_y'] = df.wafer_shift_y + df['tc_y_center']
        df['wx_center'] = df.wafer_shift_x + univ_wcenterx # fourth vertex (center) for cu/cv=(3,3)
        df['wy_center'] = df.wafer_shift_y + univ_wcentery # fourth vertex (center) for cu/cv=(3,3)

        df = self.cell_location(df)
        # df = self.cell_location_shift(df)
        print('inside 0')
        angle = 0 # must be changed for different wafer orientations
        for kloc in ('UL', 'UR', 'B'):
            cx_d, cy_d = df[df.cloc==kloc]['tc_x'], df[df.cloc==kloc]['tc_y']
            wc_x, wc_y = df[df.cloc==kloc]['wx_center'], df[df.cloc==kloc]['wy_center']
            print('inside 1 ', kloc)
            # x0 refers to the x position the lefmost, down corner all diamonds (TCs)
            # x1, x2, x3 are defined in a counter clockwise fashion
            # same for y0, y1, y2 and y3
            # tc positions refer to the center of the diamonds
            if kloc == 'UL':
                x0.update({kloc: cx_d - self.cellDistX/2})
            elif kloc == 'UR':
                x0.update({kloc: cx_d - self.cellDistX/2})
            else:
                x0.update({kloc: cx_d - self.cellDistX})
            print('inside 2 ', kloc)
            x1.update({kloc: x0[kloc][:] + self.cellDistX})
            if kloc in ('UL', 'UR'):
                x2.update({kloc: x1[kloc]})
                x3.update({kloc: x0[kloc]})
            else:
                x2.update({kloc: x1[kloc] + self.cellDistX})
                x3.update({kloc: x1[kloc]})
            print('inside 2 ', kloc)
            if kloc == 'UL':
                y0.update({kloc: cy_d - (self.cellDistY/2 + self.cellDistX*self.t30)})
            elif kloc == 'UR':
                y0.update({kloc: cy_d - (self.cellDistY/2)})
            else:
                y0.update({kloc: cy_d})
            print('inside 3 ', kloc)
            if kloc in ('UR', 'B'):
                y1.update({kloc: y0[kloc][:] - self.cellDistY})
            else:
                y1.update({kloc: y0[kloc][:] + self.cellDistY})
            if kloc in ('B'):
                y2.update({kloc: y0[kloc][:]})
            else:
                y2.update({kloc: y1[kloc][:] + 2*self.cellDistY})
            if kloc in ('UL', 'UR'):
                y3.update({kloc: y0[kloc][:] + 2*self.cellDistY})
            else:
                y3.update({kloc: y0[kloc][:] + self.cellDistY})
            print('inside 4 ', kloc)
            x0[kloc], y0[kloc] = self.rotate(angle, x0[kloc], y0[kloc], wc_x, wc_y)
            x1[kloc], y1[kloc] = self.rotate(angle, x1[kloc], y1[kloc], wc_x, wc_y)
            x2[kloc], y2[kloc] = self.rotate(angle, x2[kloc], y2[kloc], wc_x, wc_y)
            x3[kloc], y3[kloc] = self.rotate(angle, x3[kloc], y3[kloc], wc_x, wc_y)
            print('inside 5 ', kloc)
            keys = ['pos0','pos1','pos2','pos3']
            xaxis.update({
                kloc: pd.concat([x0[kloc],x1[kloc],x2[kloc],x3[kloc]],
                                   axis=1, keys=keys)})
            yaxis.update(
                {kloc: pd.concat([y0[kloc],y1[kloc],y2[kloc],y3[kloc]],
                                    axis=1, keys=keys)})
            print('inside 6 ', kloc)
            xaxis[kloc]['new'] = [[[[round(val, 3) for val in sublst]]]
                                     for sublst in xaxis[kloc].values.tolist()]
            yaxis[kloc]['new'] = [[[[round(val, 3) for val in sublst]]]
                                     for sublst in yaxis[kloc].values.tolist()]
            xaxis[kloc] = xaxis[kloc].drop(keys, axis=1)
            yaxis[kloc] = yaxis[kloc].drop(keys, axis=1)
            print('inside 7 ', kloc)
        df['diamond_x'] = pd.concat(xaxis.values())
        df['diamond_y'] = pd.concat(yaxis.values())
        print('inside 8 ')
        # define module corners' coordinates
        xcorners_str = ['corner1x','corner2x','corner3x','corner4x','corner5x','corner6x']
        assert len(xcorners_str) == len(xcorners)
        ycorners_str = ['corner1y','corner2y','corner3y','corner4y','corner5y','corner6y']
        assert len(ycorners_str) == len(ycorners)
        for i in range(len(xcorners)):
            df[xcorners_str[i]] = df.wafer_shift_x + xcorners[i]
        for i in range(len(ycorners)):
            df[ycorners_str[i]] = df.wafer_shift_y + ycorners[i]
        # print('inside 9 ')
        # df['hex_x'] = df[xcorners_str].values.tolist()
        # print('inside 9 a')
        # df['hex_x'] = df['hex_x'].map(lambda x: [[x]])
        # print('inside 9 b')
        # df['hex_y'] = df[ycorners_str].values.tolist()
        # print('inside 9 c')
        # df['hex_y'] = df['hex_y'].map(lambda x: [[x]])
        print('inside 10 ')
        df = df.drop(xcorners_str + ycorners_str + ['tc_x_center', 'tc_y_center'], axis=1)
        return df

    def provide(self, region=None):
        """Provides a processed geometry dataframe to the client."""
        print('check geom 0')
        if not os.path.exists(self.outpath) or self.reprocess:
            print('check geom 1')
            if self.logger is not None:
                self.logger.debug('Storing geometry data...')
            print('check geom 2')
            self.store(region)
            print('check geom 3')

        if self.dataset is None: # use cached dataset (currently this will never happen)
            print('check geom 4')
            if self.logger is not None:
                self.logger.debug('Retrieving geometry data...')
            print('check geom 5')
            ds = ak.from_parquet(self.outpath)
            print('check geom 6')
            self.dataset = self._from_parquet_to_geometry(ds, region)
            print('check geom 7')
        
        return self.dataset

    def region_selection(self, df, region=None):
        """Select a specific geometry region. Used mostly for debugging."""
        if region is not None:
            regions = ('inside', 'periphery', 'wafer')
            assert region in regions
            if region == 'inside':
                df = df[((df[self.wu]==3) & (df[self.wv]==3)) |
                        ((df[self.wu]==3) & (df[self.wv]==4)) |
                        ((df[self.wu]==4) & (df[self.wv]==3)) |
                        ((df[self.wu]==4) & (df[self.wv]==4))]
     
            elif region == 'periphery':
                df = df[((df[self.wu]==-6) & (df[self.wv]==3)) |
                        ((df[self.wu]==-6) & (df[self.wv]==4)) |
                        ((df[self.wu]==-7) & (df[self.wv]==3)) |
                        ((df[self.wu]==-8) & (df[self.wv]==2)) |
                        ((df[self.wu]==-8) & (df[self.wv]==1)) |
                        ((df[self.wu]==-7) & (df[self.wv]==2))
                        ]

            elif region == 'wafer':
                df = df[((df[self.wu]==3) & (df[self.wv]==3))]

        # df = df[df.layer<9]
        # df = df[df.waferpart==0]
        return df

    def rotate(self, angle, x, y, cx, cy):
        """Counter-clockwise rotation of 'angle' [radians]."""
        assert angle >= 0 and angle < 2 * np.pi
        ret_x = np.cos(angle)*(x-cx) - np.sin(angle)*(y-cy) + cx
        ret_y = np.sin(angle)*(x-cx) + np.cos(angle)*(y-cy) + cy
        return ret_x, ret_y

    def select(self):
        """Performs data selection for performance."""
        with up.open(self.inpath) as f:
            tree = f[ os.path.join('hgcaltriggergeomtester', 'TreeTriggerCells') ]
            if self.logger is not None:
                self.logger.info(tree.show())
            data = tree.arrays(self.readvars)
            sel = (data.zside==1) & (data.subdet==1)
            fields = data.fields[:]

            for v in (self.var.side, self.var.subd):
                fields.remove(v)
            data = data[sel][fields]
            data = data[data.layer%2==1]
            #below is correct but much slower (no operator isin in awkward)
            #this cut is anyways implemented in the skimmer
            #data = data[ak.Array([x not in params.disconnectedTriggerLayers for x in data.layer])]
            
            #data = data.drop_duplicates(subset=[self.var.cu, self.var.cv, self.var.l])
            data[self.var.wv] = data.waferv
            data[self.var.wvs] = -1 * data.waferv
            #data[self.var.c] = "#8a2be2"

        return data

    def store(self, region):
        """Stores the data selection in a parquet file for quicker access."""
        print('check store 0')
        ds = self.select()
        print('check store 1')
        if os.path.exists(self.outpath):
            os.remove(self.outpath)
        print('check store 2')
        ds = self.filter_columns(ds)
        print('check store 3')
        ak.to_parquet(ds, self.outpath)
        print('check store 4')
        self.dataset = self._from_parquet_to_geometry(ds, region)
        print('check store 5')
