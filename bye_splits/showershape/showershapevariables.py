import os
import sys
#import bye_splits
#from bye_splits import common, params
import re
import yaml
import numpy as np
import pandas as pd
import h5py
from dataclasses import dataclass
import matplotlib.pyplot as plt


file_path = 'Event_to_tc.h5'
df = pd.read_hdf(file_path, key='data', mode='r')# Read the data from the HDF5 file

class shower_shape_variables:
    def firstLayer(df_tcell_layers):
        # Combine Eevnt_ID and minimum TC_Layer into a DataFrame
        df_first_tc_layer = pd.DataFrame({'Event_ID': df_tcell_layers['Event_ID'], 'Min_TC_Layer': df_tcell_layers['TC_Layers'].apply(min)})
        return df_first_tc_layer

    def lastLayer(df_tcell_layers):
        # Combine Cluster_ID and minimum TC_Layer into a DataFrame
        df_last_tc_layer = pd.DataFrame({'Cluster_ID': df_tcell_layers['Cluster_ID'], 'Min_TC_Layer': df_tcell_layers['TC_Layers'].apply(max)})
        return df_last_tc_layer
    
    def maxLayer(c3d):
        tc_layers = df['TC_Layers']
        tc_energies = df['TC_Energy']

        # Grouping TC Layers and summing the corresponding TC Energies
        layer_energy_sum = {}
        for layer, energy in zip(tc_layers, tc_energies):
            if layer in layer_energy_sum:
                layer_energy_sum[layer] += energy
            else:
                layer_energy_sum[layer] = energy

        # Finding the TC Layer with the maximum energy sum
        max_layer = max(layer_energy_sum, key=layer_energy_sum.get)
        return max_layer

    

    '''def coreShowerLength():

        return maxlength

    def percentileLayer():

        return percentile

    def percentileTriggerCells():

        return Ntc

    def varEtaEta():

        return varee

    def sigmaEtaEtaTot():

        return sigmaee

    def sigmaEtaEtaMax():

        return sigmaeemax

    def varPhiPhi():

        return varpp

    def sigmaPhiPhiTot():

        return sigmapp

    def sigmaPhiPhiMax():

        return sigmappmax

    def varRR():
    
        return varrr
    
    def sigmaRRTot():

        return sigmarr

    def sigmaRRMax():

        return sigmarrmax'''










