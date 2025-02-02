from rdkit import Chem
from rdkit.Chem import AllChem
import numpy as np
import pandas as pd
import pickle
import argparse
#from PyFingerprint.All_Fingerprint import get_fingerprint
from PyFingerprint.fingerprint import get_fingerprint
import tensorflow as tf
# import bin.SA_Score.sascorer as sascorer
from rdkit.Contrib.SA_Score import sascorer
from rdkit.Chem import QED
from rdkit.Chem import Descriptors
from rdkit.Chem import Crippen

def argument_parser():
    parser = argparse.ArgumentParser()    
    parser.add_argument('-i', '--smiles_input', required=True, help="Input file with SMILES")
    parser.add_argument('-o', '--output_dir', required=False, default='./results', help="Output directory. Default is \'results\' directory, which overwrite the original data if existed.")
    parser.add_argument('-b', '--bit_image', default=0, type=int, help="Substructural images of the ECFP4 moleulcar bits to revise for the input SMILES. Default is 0")
    parser.add_argument('-c', '--calc_all', default=False, action='store_true', help="Calculate all the possible models not used for score prediction : Anomaly detection models for MACCS, Daylight and PubChem and classification using DNN, RF and LR models")
    
    return parser

def to_bits(data, bitlen):
    bit_list = [0]*bitlen
    for val in data:
        bit_list[val] = 1
    return bit_list

def calculate_ecfp_fingerprints(smiles_list): 
    feat_list = []
    for smi in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smi)
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
            bits = fp.ToBitString()
            feat = []
            for f in bits:
                feat.append(int(f))
            feat_list.append(feat)
        except:
            feat_list.append(np.array([float('nan')]*2048))
    return np.asarray(feat_list)

def calculate_daylight_fingerprints(smiles_list): 
    feat_list = []
    for smi in smiles_list:
        try:
            fps = get_fingerprint(smi, fp_type='standard')
            feat_list.append(fps.to_numpy().reshape(1,-1))
        except:
            feat_list.append(np.array([float('nan')]*1024).reshape(1,-1))
    return np.concatenate(feat_list,axis=0)

def calculate_pubchem_fingerprints(smiles_list): 
    feat_list = []
    for smi in smiles_list:
        try:
            fps = get_fingerprint(smi, fp_type='pubchem')
            feat_list.append(fps.to_numpy().reshape(1,-1))
        except:
            feat_list.append(np.array([float('nan')]*881).reshape(1,-1))
    return np.concatenate(feat_list,axis=0)

def calculate_maccs_fingerprints(smiles_list): 
    feat_list = []
    for smi in smiles_list:
        try:
            fps = get_fingerprint(smi, fp_type='maccs')
            feat_list.append(fps.to_numpy().reshape(1,-1))
        except:
            feat_list.append(np.array([float('nan')]*166).reshape(1,-1))
    return np.concatenate(feat_list,axis=0)

def load_sklrn_m(model_f):
    with open(model_f,'rb') as f:
        model = pickle.load(f)
    return model
    
    
def load_tf_m(model_f):
    model = tf.keras.models.load_model(model_f,compile=False)
    bce = tf.keras.losses.BinaryCrossentropy()
    opt = tf.keras.optimizers.Adam(learning_rate=1e-4)
    model.compile(optimizer=opt,loss=bce,metrics=['accuracy',bce])
    
    return model
    
    
def _get_molecular_prop_(mol):
    sa = sascorer.calculateScore(mol)
    qed = QED.qed(mol)
    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    return sa, qed, mw, logp


def get_molecular_prop(smiles_list):
    prop_df = pd.DataFrame({},index=smiles_list,columns=['SA','QED','MW','LogP'])
    for smi in smiles_list:
        try:
            mol = Chem.MolFromSmiles(smi)
            sa, qed, mw, logp = _get_molecular_prop_(mol)
        except:
            sa, qed, mw, logp = None, None, None, None
        prop_df.loc[smi,:] = [sa, qed, mw, logp]
    return prop_df