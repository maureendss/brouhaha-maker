#!/usr/bin/env python

import pandas as pd
import os



def create_df(gold, snr_list):
    df=pd.read_csv(gold)
    df["subtype"] = df["subtype"].apply(lambda x : "original")
    wn_dfs=[df]
    for s in snr_list:
        df_tmp = df.copy(deep=True)
        df_tmp["id"] = df_tmp["id"].apply(lambda x: "".join([s.replace('-', ''),str(x)]))
        df_tmp["filename"] = df_tmp["filename"].apply(lambda x: "_".join([str(x),"wn"+s]))
        df_tmp["subtype"] = df_tmp["subtype"].apply(lambda x : "wn"+s)
        
        wn_dfs.append(df_tmp)

    df = pd.concat(wn_dfs)
    #    for d in wn_dfs:
    #        df = df.append(d)
    return df
        



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", help="path to the directory")
    parser.add_argument("og_gold", type=str, help="gold_csv")    
    parser.add_argument("--snr_name_list", type=str, default="25 25-625 26-25 26-875 27-5 28-125 28-75 29-375 30", help="List (space separated) of the (rounded) snr that will be used to update the gold")
 
    parser.parse_args()
    args, leftovers = parser.parse_known_args()
     
    snr_list=[x for x in args.snr_name_list.split(' ')]

    df = create_df(args.og_gold, snr_list)
    df.to_csv(os.path.join(args.output_dir,"gold.csv"), index=False)
