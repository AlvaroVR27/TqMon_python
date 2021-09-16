#!/usr/bin/env python
# coding: utf-8

# In[ ]:


__author__ = "Hector Garcia Carton"
__copyright__ = "Copyright (C) 2021 Hector Garcia Carton"
__license__ = "Public Domain"
__version__ = "1.6"

import asammdf as mdf
import pandas as pd
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk
import numpy as np
import numexpr
import wheel
import canmatrix
import lxml
import lz4


class Entryreturnvalue (tk.Entry):
    def __init__(self, parent,row=None, column=None, padx=None):
        tk.Entry.__init__(self, parent,width=10)
        vcmd = (self.register(self.onValidate),'%S')
        self.value=tk.StringVar()
        self.config(textvariable=self.value, validate="key", validatecommand=vcmd)
        self.grid(row=row,column=column,padx=padx)
    def valuereturn(self):
        return (self.value.get())
    def onValidate(self, S):
        try:
            if S=='.' or type(int(S))==int or S=='':
                return True
            else:
                self.bell()
                return False
        except ValueError:
            self.bell()
            return False


class Listbox_enginetype (tk.Listbox):
    def __init__(self, parent):
        tk.Listbox.__init__(self, parent,height=2)
        self.insert(1,"K9K Gen8 Full")
        self.pack(side="top", fill="x")
        self.insert(2,'Gasoline')
        self.pack(side="top", fill="x")
        self.select_set(0)
        self.event_generate("<<ListboxSelect>>")
        self.config(exportselection=False)

    def valuereturn(self):
        self.value=(self.get(self.curselection()))


class Listbox_c1a (tk.Listbox):
    def __init__(self, parent):
        tk.Listbox.__init__(self, parent,height=2)
        self.insert(1,"C1A")
        self.pack(side="top", fill="x")
        self.insert(2,"Other")
        self.pack(side="top", fill="x")
        self.select_set(0)
        self.event_generate("<<ListboxSelect>>")
        self.config(exportselection=False)
    def valuereturn(self):
        self.value=(self.get(self.curselection()))


def increments (df,label):
    increment=pd.DataFrame((df[label].max()-df[label].min()),index=["Difference between Max and Min values"],columns=[label])
    return increment


def max_2_labels (df,label1,label2):
    max_serie=df[[label1,label2]].max(axis=1)
    return max_serie


def to_pd (root, raster_cho, label_filter=None):
    if label_filter==None:
        root=tkinter.Tk()
        filtre_file=tkinter.filedialog.askopenfilename(parent=root,)
        root.destroy()
        filtre=list(open(filtre_file).read().split("\n"))
    else:
        filtre=list(label_filter)
    records_name=tk.filedialog.askopenfilenames(parent=root, title="Select Record Files",filetypes=[("INCA files", ".mf4 .dat")])
    i=0
    for record in records_name:
            if i==0 :
                file_df=mdf.MDF(record,remove_source_from_channel_names=True).to_dataframe(filtre,ignore_value2text_conversions=True,reduce_memory_usage=True,raster=raster_cho)
                file_df["file_name"]=record
                i+=1
            else:
                next_file=mdf.MDF(record,remove_source_from_channel_names=True).to_dataframe(filtre,ignore_value2text_conversions=True,reduce_memory_usage=True,raster=raster_cho)
                next_file["file_name"]=record
                file_df=pd.concat([file_df,next_file],sort=False)
    file_df.reset_index(inplace=True)
    return file_df


def cond_diff_abs_time_max (df,label1, label2, threshold, time_maxi, raster_cho, name, greater = True, var_compar = False):
    if var_compar:
        threshold = df[threshold]
    if greater:
        df_fil = df.loc[(df[label1] - df[label2]).abs() > threshold, :].copy()
    else:
        df_fil = df.loc[(df[label1] - df[label2]).abs() < threshold, :].copy()
    df_fil["criterion"]=(df[label1]-df[label2]).abs()
    df_fil.reset_index(inplace=True)
    df_fil["t_diff"]=np.insert(np.diff(df_fil["timestamps"]),obj=0,values=0)
    idx_sector_beg=list(df_fil.loc[df_fil["t_diff"]>(raster_cho+0.0001),:].index)
    idx_sector_file_chg=list(df_fil.loc[df_fil["t_diff"]<0,:].index)
    idx_sector_beg=idx_sector_beg+idx_sector_file_chg
    idx_sector_beg.sort()
    idx_sector_end=idx_sector_beg.copy()
    idx_sector_end=list(idx_sector_end-np.ones(len(idx_sector_end),dtype=np.int8))
    idx_sector_beg.insert(0,0)
    idx_sector_end.append(len(df_fil)-1)
    result_diag=pd.DataFrame(np.subtract((df_fil.loc[idx_sector_end,"timestamps"]).array,(df_fil.loc[idx_sector_beg,"timestamps"]).array),index=idx_sector_beg,columns=["time_length [s]"])
    result_diag=result_diag.loc[result_diag["time_length [s]"]>time_maxi,:]
    if len(result_diag.index)==0:
        result_diag["time_point [s]"]=[]
        result_diag["file"]=[]
        result_diag["deviation_max"]=[]
    else:
        result_diag["time_point [s]"]=df_fil.loc[idx_sector_beg,"timestamps"].copy()
        result_diag["file"]=df_fil.loc[idx_sector_beg,"file_name"].copy()
        deviation_max=[]
        for b,e in zip(idx_sector_beg,idx_sector_end):
            deviation_max.append(df_fil.loc[b:e,"criterion"].max())
        result_diag["deviation_max"]=pd.DataFrame(deviation_max,index=idx_sector_beg)
    columns=list(result_diag.columns)
    result_diag.columns=pd.MultiIndex.from_product([[name],columns])
    result_diag.reset_index(inplace=True,drop=True)
    return result_diag


def cond_diff_time_max (df,label1, label2, threshold, time_maxi, raster_cho, name, greater=True, var_compar=False):
    if var_compar:
        threshold = df[threshold]
    if greater:
        df_fil = df.loc[(df[label1] - df[label2]) > threshold, :].copy()
    else:
        df_fil = df.loc[(df[label1] - df[label2]) < threshold, :].copy()
    df_fil["criterion"]=(df[label1]-df[label2])
    df_fil.reset_index(inplace=True)
    df_fil["t_diff"]=np.insert(np.diff(df_fil["timestamps"]),obj=0,values=0)
    idx_sector_beg=list(df_fil.loc[df_fil["t_diff"]>(raster_cho+0.0001),:].index)
    idx_sector_file_chg=list(df_fil.loc[df_fil["t_diff"]<0,:].index)
    idx_sector_beg=idx_sector_beg+idx_sector_file_chg
    idx_sector_beg.sort()
    idx_sector_end=idx_sector_beg.copy()
    idx_sector_end=list(idx_sector_end-np.ones(len(idx_sector_end),dtype=np.int8))
    idx_sector_beg.insert(0,0)
    idx_sector_end.append(len(df_fil)-1)
    result_diag=pd.DataFrame(np.subtract((df_fil.loc[idx_sector_end,"timestamps"]).array,(df_fil.loc[idx_sector_beg,"timestamps"]).array),index=idx_sector_beg,columns=["time_length [s]"])
    result_diag=result_diag.loc[result_diag["time_length [s]"]>time_maxi,:]
    if len(result_diag.index)==0:
        result_diag["time_point [s]"]=[]
        result_diag["file"]=[]
        result_diag["deviation_max"]=[]
    else:
        result_diag["time_point [s]"]=df_fil.loc[idx_sector_beg,"timestamps"].copy()
        result_diag["file"]=df_fil.loc[idx_sector_beg,"file_name"].copy()
        deviation_max=[]
        for b,e in zip(idx_sector_beg,idx_sector_end):
            deviation_max.append(df_fil.loc[b:e,"criterion"].max())
        result_diag["deviation_max"]=pd.DataFrame(deviation_max,index=idx_sector_beg)
    columns=list(result_diag.columns)
    result_diag.columns=pd.MultiIndex.from_product([[name],columns])
    result_diag.reset_index(inplace=True,drop=True)
    return result_diag

def cond_diff_time_min (df, label1, label2, threshold, time_min, raster_cho, name):
    df_fil=df.loc[(df[label1]-df[label2])>threshold,:].copy()
    df_fil = df.loc[(df[label1] - df[label2]) > threshold, :].copy()
    df_fil["criterion"] = (df[label1] - df[label2])
    df_fil.reset_index(inplace=True)
    df_fil["t_diff"] = np.insert(np.diff(df_fil["timestamps"]), obj=0, values=0)
    idx_sector_beg = list(df_fil.loc[df_fil["t_diff"] > (raster_cho + 0.0001), :].index)
    idx_sector_file_chg = list(df_fil.loc[df_fil["t_diff"] < 0, :].index)
    idx_sector_beg = idx_sector_beg + idx_sector_file_chg
    idx_sector_beg.sort()
    idx_sector_end = idx_sector_beg.copy()
    idx_sector_end = list(idx_sector_end - np.ones(len(idx_sector_end), dtype=np.int8))
    idx_sector_beg.insert(0, 0)
    idx_sector_end.append(len(df_fil) - 1)
    result_diag = pd.DataFrame(
        np.subtract((df_fil.loc[idx_sector_end, "timestamps"]).array, (df_fil.loc[idx_sector_beg, "timestamps"]).array),
        index=idx_sector_beg, columns=["time_length [s]"])
    result_diag = result_diag.loc[result_diag["time_length [s]"] < time_min, :]
    if len(result_diag.index) == 0:
        result_diag["time_point [s]"] = []
        result_diag["file"] = []
        result_diag["deviation_max"] = []
    else:
        result_diag["time_point [s]"] = df_fil.loc[idx_sector_beg, "timestamps"].copy()
        result_diag["file"] = df_fil.loc[idx_sector_beg, "file_name"].copy()
        deviation_max = []
        for b, e in zip(idx_sector_beg, idx_sector_end):
            deviation_max.append(df_fil.loc[b:e, "criterion"].max())
        result_diag["deviation_max"] = pd.DataFrame(deviation_max, index=idx_sector_beg)
    columns = list(result_diag.columns)
    result_diag.columns = pd.MultiIndex.from_product([[name], columns])
    result_diag.reset_index(inplace=True, drop=True)
    return result_diag

def cond_diff_abs_rel_time_max (df,label1, label2, threshold, time_maxi, raster_cho, name):
    df_fil=df.loc[df[label2]!=0,:].copy()
    df_fil=df_fil.loc[((df_fil[label1]-df_fil[label2])/df_fil[label2]).abs()>threshold,:]
    df_fil["criterion"]=((df_fil[label1]-df_fil[label2])/df_fil[label2]).abs()
    df_fil.reset_index(inplace=True)
    df_fil["t_diff"]=np.insert(np.diff(df_fil["timestamps"]),obj=0,values=0)
    idx_sector_beg=list(df_fil.loc[df_fil["t_diff"]>(raster_cho+0.0001),:].index)
    idx_sector_file_chg=list(df_fil.loc[df_fil["t_diff"]<0,:].index)
    idx_sector_beg=idx_sector_beg+idx_sector_file_chg
    idx_sector_beg.sort()
    idx_sector_end=idx_sector_beg.copy()
    idx_sector_end=list(idx_sector_end-np.ones(len(idx_sector_end),dtype=np.int8))
    idx_sector_beg.insert(0,0)
    idx_sector_end.append(len(df_fil)-1)
    result_diag=pd.DataFrame(np.subtract((df_fil.loc[idx_sector_end,"timestamps"]).array,(df_fil.loc[idx_sector_beg,"timestamps"]).array),index=idx_sector_beg,columns=["time_length [s]"])
    result_diag=result_diag.loc[result_diag["time_length [s]"]>time_maxi,:]
    if len(result_diag.index)==0:
        result_diag["time_point [s]"]=[]
        result_diag["file"]=[]
        result_diag["deviation_max"]=[]
    else:
        result_diag["time_point [s]"]=df_fil.loc[idx_sector_beg,"timestamps"].copy()
        result_diag["file"]=df_fil.loc[idx_sector_beg,"file_name"].copy()
        deviation_max=[]
        for b,e in zip(idx_sector_beg,idx_sector_end):
            deviation_max.append(df_fil.loc[b:e,"criterion"].max())
        result_diag["deviation_max"]=pd.DataFrame(deviation_max,index=idx_sector_beg)
    columns=list(result_diag.columns)
    result_diag.columns = pd.MultiIndex.from_product([[name],columns])
    result_diag.reset_index(inplace=True,drop=True)
    return result_diag


def cond_abs_time_max (df,label, threshold, time_maxi, raster_cho, name):
    df_fil=df.loc[df[label].abs()>threshold,:].copy()
    df_fil["criterion"]=(df[label]).abs()
    df_fil.reset_index(inplace=True)
    df_fil["t_diff"]=np.insert(np.diff(df_fil["timestamps"]),obj=0,values=0)
    idx_sector_beg=list(df_fil.loc[df_fil["t_diff"]>(raster_cho+0.0001),:].index)
    idx_sector_file_chg=list(df_fil.loc[df_fil["t_diff"]<0,:].index)
    idx_sector_beg=idx_sector_beg+idx_sector_file_chg
    idx_sector_beg.sort()
    idx_sector_end=idx_sector_beg.copy()
    idx_sector_end=list(idx_sector_end-np.ones(len(idx_sector_end),dtype=np.int8))
    idx_sector_beg.insert(0,0)
    idx_sector_end.append(len(df_fil)-1)
    result_diag=pd.DataFrame(np.subtract((df_fil.loc[idx_sector_end,"timestamps"]).array,(df_fil.loc[idx_sector_beg,"timestamps"]).array),index=idx_sector_beg,columns=["time_length [s]"])
    result_diag=result_diag.loc[result_diag["time_length [s]"]>time_maxi,:]
    if len(result_diag.index)==0:
        result_diag["time_point [s]"]=[]
        result_diag["file"]=[]
        result_diag["deviation_max"]=[]
    else:
        result_diag["time_point [s]"]=df_fil.loc[idx_sector_beg,"timestamps"].copy()
        result_diag["file"]=df_fil.loc[idx_sector_beg,"file_name"].copy()
        deviation_max=[]
        for b,e in zip(idx_sector_beg,idx_sector_end):
            deviation_max.append(df_fil.loc[b:e,"criterion"].max())
        result_diag["deviation_max"]=pd.DataFrame(deviation_max,index=idx_sector_beg)
    columns=list(result_diag.columns)
    result_diag.columns=pd.MultiIndex.from_product([[name],columns])
    result_diag.reset_index(inplace=True,drop=True)
    return result_diag


def cond_time_max (df,label, threshold, time_maxi, raster_cho, name, greater = True, var_compar = False):
    if var_compar:
        threshold = df[threshold]
    if greater:
        df_fil = df.loc[df[label] > threshold, :].copy()
    else:
        df_fil = df.loc[df[label] < threshold, :].copy()
    df_fil["criterion"]=(df[label])
    df_fil.reset_index(inplace=True)
    df_fil["t_diff"]=np.insert(np.diff(df_fil["timestamps"]),obj=0,values=0)
    idx_sector_beg=list(df_fil.loc[df_fil["t_diff"]>(raster_cho+0.0001),:].index)
    idx_sector_file_chg=list(df_fil.loc[df_fil["t_diff"]<0,:].index)
    idx_sector_beg=idx_sector_beg+idx_sector_file_chg
    idx_sector_beg.sort()
    idx_sector_end=idx_sector_beg.copy()
    idx_sector_end=list(idx_sector_end-np.ones(len(idx_sector_end),dtype=np.int8))
    idx_sector_beg.insert(0,0)
    idx_sector_end.append(len(df_fil)-1)
    result_diag=pd.DataFrame(np.subtract((df_fil.loc[idx_sector_end,"timestamps"]).array,(df_fil.loc[idx_sector_beg,"timestamps"]).array),index=idx_sector_beg,columns=["time_length [s]"])
    result_diag=result_diag.loc[result_diag["time_length [s]"]>time_maxi,:]
    if len(result_diag.index)==0:
        result_diag["time_point [s]"]=[]
        result_diag["file"]=[]
        result_diag["deviation_max"]=[]
    else:
        result_diag["time_point [s]"]=df_fil.loc[idx_sector_beg,"timestamps"].copy()
        result_diag["file"]=df_fil.loc[idx_sector_beg,"file_name"].copy()
        deviation_max=[]
        for b,e in zip(idx_sector_beg,idx_sector_end):
            deviation_max.append(df_fil.loc[b:e,"criterion"].max())
        result_diag["deviation_max"]=pd.DataFrame(deviation_max,index=idx_sector_beg)
    columns=list(result_diag.columns)
    result_diag.columns=pd.MultiIndex.from_product([[name],columns])
    result_diag.reset_index(inplace=True,drop=True)
    return result_diag


def agr_v1 (root, labels, raster_cho, dataset):
    try:
        wait_label=tk.Label(root,text="PROCESSING...PLEASE WAIT",height=5,width=30)
        wait_label.config(fg="#2330e1")
        wait_label.pack(side="bottom", fill="x")
        file_df=to_pd (root, raster_cho, labels)
        file_df_diag_ena=file_df.loc[((file_df["Vxx_sfty_n"]>dataset["Cxx_sfty_diag_ena_n_thd"])&
                                      (file_df["Vbx_sfty_eng_aut"]==1)&
                                      (file_df["Vxx_sfty_vs"]>dataset["Cxx_sfty_vs_dsb_vs_thd"])),:].copy()
        result_inc=pd.DataFrame()
        result_list=[]
        file_df_paf=file_df_diag_ena.loc[file_df_diag_ena["Vxx_acel_pdl_rat"]>0.9,:].copy()
        labels_inc=["Vxx_sfty_tqi_sp_ctr_2","Vxx_sfty_esti_tqi_ctr_2","Vsx_sfty_esti_tqi_vld","Vsx_sfty_eng_tql_vld",
                    "Vsx_sfty_min_driv_tqe_vld","Vsx_sfty_max_tqe_vld","Vsx_sfty_is_req_vld"]
        for i in labels_inc:
            result_inc = pd.concat([result_inc, increments(df=file_df,label=i)], axis=1, join="outer")
        time_maxi=0
        labels_diff_abs_rel_time_max=[["Vxx_sfty_acel_pdl_fmt_fac","Vxx_acel_pdl_fmt_fac","Seuil_%_AGR_v1"],
                                      ["Vxx_sfty_acel_pdl_fmt_fac_eco","Vxx_acel_pdl_fmt_fac_eco","Seuil_%_AGR_v1"],
                                      ["Vxx_sfty_acel_pdl_fmt_fac_off_road","Vxx_acel_pdl_fmt_fac_off_road","Seuil_%_AGR_v1"],
                                      ["Vxx_sfty_acel_pdl_fmt_fac_snw","Vxx_acel_pdl_fmt_fac_snw","Seuil_%_AGR_v1"],
                                      ["Vxx_sfty_acel_pdl_fmt_fac_spt","Vxx_acel_pdl_fmt_fac_spt","Seuil_%_AGR_v1"],
                                      ["Vxx_sfty_acel_pdl_pwt_sp","Vxx_acel_pdl_pwt_sp","Seuil_%_AGR_v1"],
                                      ["Vxx_sfty_driv_pwt_sp","Vxx_driv_pwt_sp","Seuil_%_AGR_v1"]]
        for a,b,c in labels_diff_abs_rel_time_max:
            result_list.append(cond_diff_abs_rel_time_max(df=file_df_paf,label1=a,label2=b,threshold=dataset[c],time_maxi=time_maxi,
                                                          raster_cho=raster_cho,name=str("| "+a+" - "+b+" |")))
        time_maxi=0
        file_df_paf["max_Vxx_min_driv_tqe_Vxx_min_avl_tqe"]=max_2_labels (file_df_paf,"Vxx_min_driv_tqe","Vxx_min_avl_tqe")
        file_df_paf["minus_Vxx_ajs_cor_dyn_tqe"]=file_df_paf["Vxx_ajs_cor_dyn_tqe"].multiply(-1)
        labels_diff_abs_time_max=[["Vxx_sfty_min_driv_tqe","max_Vxx_min_driv_tqe_Vxx_min_avl_tqe","Cxx_sfty_dif_min_driv_err"],
                                  ["Vxx_sfty_max_eco_tqe","Vxx_max_stat_avl_tqe","Cxx_sfty_dif_max_tqe_err"],
                                  ["Vxx_sfty_tkof_tqe_cor","Vxx_tkof_tqe_cor","Seuil_Nm_AGR_v1"],
                                  ["Vxx_sfty_lim_driv_tqe_sp","Vxx_lim_driv_tqe_sp","Seuil_Nm_AGR_v1"],
                                  ["Vxx_sfty_ajs_modu_tqe","Vxx_ajs_modu_tqe_sp","Seuil_Nm_AGR_v1"],
                                  ["Vxx_sfty_ajs_cor_dyn_tqe","minus_Vxx_ajs_cor_dyn_tqe","Seuil_Nm_AGR_v1"],
                                  ["Vxx_sfty_arb_tqe","Vxx_arb_tqe_sp","Seuil_Nm_AGR_v1"],
                                  ["Vxx_sfty_eng_tql","Vxx_eng_tql","Cxx_sfty_eng_tql_chr_thd"],
                                  ["Vxx_sfty_is_tqe_sp","Vxx_is_tqe_sp","Seuil_Nm_AGR_v1"],
                                  ["Vxx_sfty_ac_pow_max","Vxx_ac_pow","Seuil_W_AGR_v1"],
                                  ["Vxx_sfty_alt_pow_max","Vxx_fil_alt_pow","Seuil_W_AGR_v1"],
                                  ["Vxx_tqi_sp","Vxx_sfty_tqi_sp","Seuil_Nm_AGR_v1"]]
        for a,b,c in labels_diff_abs_time_max:
            result_list.append(cond_diff_abs_time_max(df=file_df_paf,label1=a,label2=b,threshold=dataset[c]/2,time_maxi=time_maxi,
                                                      raster_cho=raster_cho,name=str("| "+a+" - "+b+" |")))
        result_list.insert(0,result_inc)
        try:
            save_name=tk.filedialog.asksaveasfilename(parent=root,title="Save Report As",defaultextension='.xlsx',
                                                        initialfile="agr_v1",filetypes=[("Excel files", ".xlsx")])
            excelwriter = pd.ExcelWriter(save_name,engine="xlsxwriter")
            workbook=excelwriter.book
            number_format=workbook.add_format({'num_format':'# ##0.00'})
            c=0
            for i in result_list:
                if c==0:
                    i.to_excel(excelwriter,startcol=c,freeze_panes=(2,0),sheet_name="AGR_v1")
                    excelwriter.sheets["AGR_v1"].set_column(0,0,36)
                    excelwriter.sheets["AGR_v1"].set_column(1,len(i.columns),20,number_format)
                else:
                    i.to_excel(excelwriter,startcol=c,freeze_panes=(2,0),sheet_name="AGR_v1")
                    excelwriter.sheets["AGR_v1"].set_column(c+1,c+len(i.columns),15,number_format)
                c+=(len(i.columns)+2)
            excelwriter.save()
            wait_label.destroy()
            excelwriter.close()
            w=175
            h=75
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root2=tk.Toplevel()
            root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
            frame_new=tk.Frame(root2)
            frame_new.pack(expand=True,fill="both")
            message_finish=tk.Label(frame_new,text="Done!",font='Helvetica 18 bold')
            message_finish.config(fg='#14890a',anchor="n")
            message_finish.pack(side="top",fill="x")
            button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
            button_finish.pack(pady=5,side="bottom")
            frame_new.grab_set()
            root2.mainloop()
        except:
            wait_label.destroy()
            w=200
            h=100
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root2=tk.Toplevel()
            root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
            frame_new=tk.Frame(root2)
            frame_new.pack(expand=True,fill="both")
            message_finish=tk.Label(frame_new,text="Oops!\n Something went wrong.",font='Helvetica 12 bold')
            message_finish.config(fg='#d60606',anchor="n")
            message_finish.pack(side="top",fill="x")
            button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
            button_finish.pack(pady=5,side="bottom")
            frame_new.grab_set()
            root2.mainloop()
            pass
    except:
        wait_label.destroy()
        w=200
        h=100
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        root2=tk.Toplevel()
        root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
        frame_new=tk.Frame(root2)
        frame_new.pack(expand=True,fill="both")
        message_finish=tk.Label(frame_new,text="Oops!\n Something went wrong.",font='Helvetica 12 bold')
        message_finish.config(fg='#d60606',anchor="n")
        message_finish.pack(side="top",fill="x")
        button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
        button_finish.pack(pady=5,side="bottom")
        frame_new.grab_set()
        root2.mainloop()
        pass


def agr_v2_v3_v5 (root, labels, raster_cho, dataset, c1a):
    try:
        wait_label=tk.Label(root,text="PROCESSING...PLEASE WAIT",height=5,width=30)
        wait_label.config(fg="#2330e1")
        wait_label.pack(side="bottom", fill="x")
        file_df=to_pd (root, raster_cho, labels)
        file_df_diag_ena=file_df.loc[((file_df["Vxx_sfty_n"]>dataset["Cxx_sfty_diag_ena_n_thd"])&
                                      (file_df["Vbx_sfty_eng_aut"]==1)&
                                      (file_df["Vxx_sfty_vs"]>dataset["Cxx_sfty_vs_dsb_vs_thd"])),:].copy()
        result_inc=pd.DataFrame()
        result_list=[]
        labels_inc=["Vxx_sfty_tqi_sp_ctr_2","Vxx_sfty_esti_tqi_ctr_2","Vsx_sfty_esti_tqi_vld","Vsx_sfty_eng_tql_vld",
                    "Vsx_sfty_min_driv_tqe_vld","Vsx_sfty_max_tqe_vld","Vsx_sfty_is_req_vld"]
        for i in labels_inc:
            result_inc = pd.concat([result_inc, increments(df=file_df,label=i)], axis=1, join="outer")
        file_df_diag_ena["max_Vxx_min_driv_tqe_Vxx_min_avl_tqe"]=max_2_labels(file_df_diag_ena,"Vxx_min_driv_tqe","Vxx_min_avl_tqe")
        time_maxi=0.2
        labels_diff_abs_time_max=[["Vxx_sfty_min_driv_tqe","max_Vxx_min_driv_tqe_Vxx_min_avl_tqe","Cxx_sfty_dif_min_driv_err"],
                                  ["Vxx_sfty_max_eco_tqe","Vxx_max_stat_avl_tqe","Cxx_sfty_dif_max_tqe_err"],
                                  ["Vxx_sfty_eng_tql","Vxx_eng_tql","Cxx_sfty_eng_tql_chr_thd"],
                                  ["Vxx_lvl1_sfty_tqi_sp_40ms","Vxx_sfty_tqi_sp","Cmp_sfty_tqi_req_pos_err"],
                                  ["Vxx_arb_no_agb_tqe","Vxx_sfty_arb_no_agb_tqe","Cmp_sfty_tqi_req_pos_err"]]
        for a,b,c in labels_diff_abs_time_max:
            result_list.append(cond_diff_abs_time_max(df=file_df_diag_ena,label1=a,label2=b,threshold=dataset[c]/2,
                                                      time_maxi=time_maxi,raster_cho=raster_cho,name=str("| "+a+" - "+b+" |")))
        if c1a=="C1A":
            a="Vxx_sfty_crk_esti_tqe"
            b="Vxx_esti_tqe_wit_dly"
            c="Cmp_sfty_tqi_req_pos_err"
            result_list.append(cond_diff_abs_time_max(df=file_df_diag_ena,label1=a,label2=b,threshold=dataset[c]/2,
                                                      time_maxi=time_maxi,raster_cho=raster_cho,name=str("| "+a+" - "+b+" |")))
        time_maxi=0.2
        labels_diff_time_max=[["Vxx_lvl2_tqi_sp_thd","Vxx_lvl1_sfty_tqi_sp","Cmp_tqi_sp_sfty_ofs"]]
        for a,b,c in labels_diff_time_max:
            result_list.append(cond_diff_time_max(df=file_df_diag_ena,label1=b,label2=a,threshold=-dataset[c]/2,time_maxi=time_maxi,
                                                  raster_cho=raster_cho,name=str(a+" - "+b)))
        time_maxi=0.2
        labels_abs_time_max=[["Vxx_sfty_tqi_esti_sp_dif","Cmp_sfty_tqi_req_pos_err"]]
        for a,c in labels_abs_time_max:
            result_list.append(cond_abs_time_max (df=file_df_diag_ena,label=a, threshold=dataset[c]/2, time_maxi=time_maxi,
                                                  raster_cho=raster_cho, name=str("| "+a+" |")))
        time_maxi=0.2
        if c1a=="Other":
            a="Vxx_sfty_dif_abv_esti_tqe"
            c="Cmp_sfty_tqi_req_pos_err"
            result_list.append(cond_time_max (df=file_df_diag_ena,label=a, threshold=dataset[c]/2, time_maxi=time_maxi,
                                              raster_cho=raster_cho, name=str(a)))
        result_list.insert(0,result_inc)
        try:
            save_name=tk.filedialog.asksaveasfilename(parent=root,title="Save Report As",defaultextension='.xlsx',
                                                      initialfile="agr_v2_v3_v5",filetypes=[("Excel files", ".xlsx")])
            excelwriter = pd.ExcelWriter(save_name,engine="xlsxwriter")
            workbook=excelwriter.book
            number_format=workbook.add_format({'num_format':'# ##0.00'})
            c=0
            for i in result_list:
                if c==0:
                    i.to_excel(excelwriter,startcol=c,freeze_panes=(2,0),sheet_name="AGR_v2_v3_v5")
                    excelwriter.sheets["AGR_v2_v3_v5"].set_column(0,0,36)
                    excelwriter.sheets["AGR_v2_v3_v5"].set_column(1,len(i.columns),20,number_format)
                else:
                    i.to_excel(excelwriter,startcol=c,freeze_panes=(2,0),sheet_name="AGR_v2_v3_v5")
                    excelwriter.sheets["AGR_v2_v3_v5"].set_column(c+1,c+len(i.columns),15,number_format)
                c+=(len(i.columns)+2)
            excelwriter.save()
            wait_label.destroy()
            excelwriter.close()
            w=175
            h=75
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root2=tk.Toplevel()
            root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
            frame_new=tk.Frame(root2)
            frame_new.pack(expand=True,fill="both")
            message_finish=tk.Label(frame_new,text="Done!",font='Helvetica 18 bold')
            message_finish.config(fg='#14890a',anchor="n")
            message_finish.pack(side="top",fill="x")
            button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
            button_finish.pack(pady=5,side="bottom")
            frame_new.grab_set()
            root2.mainloop()
        except:
            wait_label.destroy()
            w=200
            h=100
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root2=tk.Toplevel()
            root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
            frame_new=tk.Frame(root2)
            frame_new.pack(expand=True,fill="both")
            message_finish=tk.Label(frame_new,text="Oops!\n Something went wrong.",font='Helvetica 12 bold')
            message_finish.config(fg='#d60606',anchor="n")
            message_finish.pack(side="top",fill="x")
            button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
            button_finish.pack(pady=5,side="bottom")
            frame_new.grab_set()
            root2.mainloop()
            pass
    except:
        wait_label.destroy()
        w=200
        h=100
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        root2=tk.Toplevel()
        root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
        frame_new=tk.Frame(root2)
        frame_new.pack(expand=True,fill="both")
        message_finish=tk.Label(frame_new,text="Oops!\n Something went wrong.",font='Helvetica 12 bold')
        message_finish.config(fg='#d60606',anchor="n")
        message_finish.pack(side="top",fill="x")
        button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
        button_finish.pack(pady=5,side="bottom")
        frame_new.grab_set()
        root2.mainloop()
        pass


def perf_v2 (root, labels, raster_cho, dataset, c1a, engine):
    try:
        wait_label=tk.Label(root,text="PROCESSING...PLEASE WAIT",height=5,width=30)
        wait_label.config(fg="#2330e1")
        wait_label.pack(side="bottom", fill="x")
        file_df=to_pd (root, raster_cho, labels)
        file_df_paf = pd.DataFrame()
        margen = 3
        if engine == "K9K Gen8 Full":
            file_df_diag_ena=file_df.loc[((file_df["Vxx_sfty_n"]>dataset["Cxx_sfty_diag_ena_n_thd"])&
                                      (file_df["Vbx_sfty_eng_aut"]==1)&
                                      (file_df["Vxx_sfty_vs"]>dataset["Cxx_sfty_vs_dsb_vs_thd"])),:].copy()
            file_df_paf = file_df_diag_ena.loc[((file_df_diag_ena["Vxx_acel_pdl_rat"] > 0.9) &
                                                ((file_df_diag_ena["Vxx_max_dyn_avl_tqe"] + margen) > file_df_diag_ena[
                                                    "Vxx_max_stat_avl_tqe"])), :].copy()

            combustion_mode = [3, 4, 5, 8, 20, 21, 23, 11, 13, 26]
            comb_mode_dict = {3: "hdoc_hpuncool", 4: "hscr_hpuncool", 5: "mscr_hpuncool", 8: "nowup_hpuncool",
                              20: "hscr_mxuncool", 21: "mscr_mxuncool", 23: "nowup_mxcool", 11: "dénox", 13: "désox",
                              26: "rgn"}
            try:
                save_name = tk.filedialog.asksaveasfilename(parent=root, title="Save Report As",
                                                            defaultextension='.xlsx',
                                                            initialfile="perf_v2", filetypes=[("Excel files", ".xlsx")])
                excelwriter = pd.ExcelWriter(save_name, engine="xlsxwriter")
                workbook = excelwriter.book
                number_format = workbook.add_format({'num_format': '# ##0.00'})
                for mode in combustion_mode:
                    result_inc = pd.DataFrame()
                    result_list = []
                    file_df_paf_mode = file_df_paf.loc[file_df_paf["Vnx_cmb_param_set_crt"] == mode, :].copy()
                    labels_inc = ["Vxx_sfty_tqi_sp_ctr_2", "Vxx_sfty_esti_tqi_ctr_2", "Vsx_sfty_esti_tqi_vld"]
                    for i in labels_inc:
                        result_inc = pd.concat([result_inc, increments(df=file_df, label=i)], axis=1, join="outer")
                    time_maxi = 0.5
                    file_df_paf_mode["Total_inj_quantity_lvl1"] = file_df_paf_mode.loc[:,
                                                                  ["Vxx_fms_fp1", "Vxx_fms_fp2", "Vxx_fms_fim_main",
                                                                   "Vxx_fms_faf", "Vxx_fms_fpo"]].sum(axis=1)
                    file_df_paf_mode["Total_inj_quantity_lvl2"] = file_df_paf_mode.loc[:,
                                                                  ["Vxx_sfty_fms_fp4", "Vxx_sfty_fms_fp3",
                                                                   "Vxx_sfty_fms_fim_main",
                                                                   "Vxx_sfty_fms_faf", "Vxx_sfty_fms_fpo"]].sum(axis=1)
                    labels_diff_abs_time_max = [["Vxx_fms_fp1", "Vxx_sfty_fms_fp4", "Ecart_pinj_PERFO_v2 [mg/cp]"],
                                                ["Vxx_fms_fp2", "Vxx_sfty_fms_fp3", "Ecart_pinj_PERFO_v2 [mg/cp]"],
                                                ["Vxx_fms_fim_main", "Vxx_sfty_fms_fim_main",
                                                 "Ecart_main_inj_PERFO_v2 [mg/cp]"],
                                                ["Vxx_fms_faf", "Vxx_sfty_fms_faf", "Ecart_pinj_PERFO_v2 [mg/cp]"],
                                                ["Vxx_fms_fpo", "Vxx_sfty_fms_fpo", "Ecart_pinj_PERFO_v2 [mg/cp]"],
                                                ["Vxx_tqi_fim_tot", "Vxx_sfty_fms_tot_efy",
                                                 "Ecart_tot_inj_PERFO_v2 [mg/cp]"],
                                                ["Total_inj_quantity_lvl1", "Total_inj_quantity_lvl2",
                                                 "Ecart_tot_inj_PERFO_v2 [mg/cp]"]]
                    for a, b, c in labels_diff_abs_time_max:
                        result_list.append(
                            cond_diff_abs_time_max(df=file_df_paf_mode, label1=a, label2=b, threshold=dataset[c] / 2,
                                                   time_maxi=time_maxi, raster_cho=raster_cho,
                                                   name=str("| " + a + " - " + b + " |")))
                    time_maxi = 0
                    labels_diff_abs_time_max = [
                        ["Vxx_lvl1_sfty_tqi_sp_40ms", "Vxx_sfty_tqi_sp", "Cmp_sfty_tqi_req_pos_err"],
                        ["Vxx_lvl1_sfty_tqi_sp", "Vxx_sfty_tqi_sp", "Cmp_sfty_tqi_req_pos_err"],
                        ["Vxx_arb_no_agb_tqe", "Vxx_sfty_arb_no_agb_tqe", "Cmp_sfty_tqi_req_pos_err"],
                        ["Vxx_driv_pwt_sp_wo_dly", "Vxx_sfty_driv_adas_pwt_sp", "Cxx_sfty_mux_driv_pwt_sp_ofs"]]
                    for a, b, c in labels_diff_abs_time_max:
                        result_list.append(
                            cond_diff_abs_time_max(df=file_df_paf_mode, label1=a, label2=b, threshold=dataset[c] / 2,
                                                   time_maxi=time_maxi, raster_cho=raster_cho,
                                                   name=str("| " + a + " - " + b + " |")))
                    if c1a == "C1A":
                        a = "Vxx_sfty_crk_esti_tqe"
                        b = "Vxx_esti_tqe_wit_dly"
                        c = "Cmp_sfty_tqi_req_pos_err"
                        time_maxi = 0
                        result_list.append(
                            cond_diff_abs_time_max(df=file_df_paf_mode, label1=a, label2=b, threshold=dataset[c] / 2,
                                                   time_maxi=time_maxi, raster_cho=raster_cho,
                                                   name=str("| " + a + " - " + b + " |")))
                    time_maxi = 0
                    labels_abs_time_max = [["Vxx_sfty_tqi_esti_sp_dif", "Cmp_sfty_tqi_req_pos_err"],
                                           ["Vxx_sfty_tqi_int_err", "Seuil_Nms_PERFO_v2"]]
                    for a, c in labels_abs_time_max:
                        result_list.append(cond_abs_time_max(df=file_df_paf_mode, label=a, threshold=dataset[c] / 2,
                                                             time_maxi=time_maxi,
                                                             raster_cho=raster_cho, name=str("| " + a + " |")))
                    if c1a == "Other":
                        time_maxi = 0
                        a = "Vxx_sfty_dif_abv_esti_tqe"
                        c = "Cmp_sfty_tqi_req_pos_err"
                        result_list.append(
                            cond_time_max(file_df_paf_mode, label=a, threshold=dataset[c] / 2, time_maxi=time_maxi,
                                          raster_cho=raster_cho, name=str(a)))
                    result_list.insert(0, result_inc)
                    c = 0
                    for i in result_list:
                        if c == 0:
                            i.to_excel(excelwriter, startcol=c, freeze_panes=(2, 0), sheet_name=comb_mode_dict[mode])
                            excelwriter.sheets[comb_mode_dict[mode]].set_column(0, 0, 36)
                            excelwriter.sheets[comb_mode_dict[mode]].set_column(1, len(i.columns), 20, number_format)
                        else:
                            i.to_excel(excelwriter, startcol=c, freeze_panes=(2, 0), sheet_name=comb_mode_dict[mode])
                            excelwriter.sheets[comb_mode_dict[mode]].set_column(c + 1, c + len(i.columns), 15,
                                                                                number_format)
                        c += (len(i.columns) + 2)
                excelwriter.save()
                wait_label.destroy()
                excelwriter.close()
                w = 175
                h = 75
                ws = root.winfo_screenwidth()
                hs = root.winfo_screenheight()
                x = (ws / 2) - (w / 2)
                y = (hs / 2) - (h / 2)
                root2 = tk.Toplevel()
                root2.geometry("%dx%d+%d+%d" % (w, h, x, y))
                frame_new = tk.Frame(root2)
                frame_new.pack(expand=True, fill="both")
                message_finish = tk.Label(frame_new, text="Done!", font='Helvetica 18 bold')
                message_finish.config(fg='#14890a', anchor="n")
                message_finish.pack(side="top", fill="x")
                button_finish = tk.Button(frame_new, text="OK", width=10, command=root2.destroy, bd=5)
                button_finish.pack(pady=5, side="bottom")
                frame_new.grab_set()
                root2.mainloop()
            except:
                wait_label.destroy()
                w = 200
                h = 100
                ws = root.winfo_screenwidth()
                hs = root.winfo_screenheight()
                x = (ws / 2) - (w / 2)
                y = (hs / 2) - (h / 2)
                root2 = tk.Toplevel()
                root2.geometry("%dx%d+%d+%d" % (w, h, x, y))
                frame_new = tk.Frame(root2)
                frame_new.pack(expand=True, fill="both")
                message_finish = tk.Label(frame_new, text="Oops!\n Something went wrong.", font='Helvetica 12 bold')
                message_finish.config(fg='#d60606', anchor="n")
                message_finish.pack(side="top", fill="x")
                button_finish = tk.Button(frame_new, text="OK", width=10, command=root2.destroy, bd=5)
                button_finish.pack(pady=5, side="bottom")
                frame_new.grab_set()
                root2.mainloop()
                pass
        elif engine == "Gasoline":
            file_df_diag_ena=file_df.loc[((file_df["Vxx_sfty_n"]>dataset["Cxx_sfty_diag_ena_n_thd"])&
                                      (file_df["Vxx_sfty_vs"]>dataset["Cxx_sfty_vs_dsb_vs_thd"])),:].copy()
            file_df_paf = file_df_diag_ena.loc[((file_df_diag_ena["Vxx_max_dyn_avl_tqe"] + margen) >
                                                              file_df_diag_ena["Vxx_max_stat_avl_tqe"]), :].copy()
            try:
                # TODO: PERF V2 ENGINE Gasoline
                result_inc = pd.DataFrame()
                result_list=[]
                labels_inc = ["Vxx_sfty_tqi_sp_ctr_2", "Vxx_sfty_esti_tqi_ctr_2", "Vsx_sfty_esti_tqi_vld"]
                for i in labels_inc:
                    result_inc = pd.concat([result_inc, increments(df=file_df,label=i)], axis=1, join="outer")

                # TEST 1
                time_max = 0
                on_delay_1 = 5 # Real delay to wait for the condition (times raster_cho)
                on_delay_2 = 7 # Delay for the second condition in seconds
                a = "Vxx_lvl1_sfty_tqi_sp_40ms"
                b = "Vxx_sfty_tqi_sp"
                c = "_Cmp_sfty_tqi_rec_pos_err"
                name = 'Test 1' + str(a+" - "+b)
                interest_list = []
                interest_list.append(cond_diff_time_max(df=file_df_paf, label1=a, label2=b, threshold=c,time_maxi=time_max,
                                                            raster_cho=raster_cho,name=name,greater=True, var_compar=True))

                for results in interest_list:
                    time_point = results[name,'time_point [s]']
                    time_length = results[name,'time_length [s]']
                    for i in range(time_point.shape[0]):
                        if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + on_delay_1 * raster_cho) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vbx_sfty_df_tqi_sp_chr'] != 1)].empty:
                            results.drop([i], axis=0, inplace=True)  # Valid result
                        elif file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + on_delay_2) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vsx_sfty_esti_tqi_vld'] != 'Nsx_vld_nok_0')].empty:
                            results.drop([i], axis=0, inplace=True) # Valid result
                result_list.extend(interest_list)


                # TEST 2
                time_max = 0
                delay_1 = 0.5
                a = "Vxx_sfty_tqi_esti_sp_dif"
                b = "Vxx_sfty_esti_err_max"
                name = 'Test 2 ' + a
                interest_list = []
                interest_list.append(cond_time_max(df=file_df_paf, label=a, threshold=b, time_maxi=time_max,
                                                        raster_cho=raster_cho, name=name, greater=True, var_compar=True))
                for results in interest_list:
                    time_point = results[name, 'time_point [s]']
                    time_length = results[name, 'time_length [s]']
                    for i in range(time_point.shape[0]):
                        if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + delay_1) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vbx_sfty_df_esti_tqi_chr'] != 1)].empty:
                            results.drop([i], axis=0, inplace=True)
                        elif file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + on_delay_2) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vsx_sfty_esti_tqi_vld'] != 'Nsx_vld_nok_0')].empty:
                            results.drop([i], axis=0, inplace=True)
                result_list.extend(interest_list)

                # TEST 3
                time_max = 0
                a = "Vxx_sfty_tqi_int_err"
                b = "Cxx_sfty_tqi_int_tol"
                name = 'Test 3 '+a
                interest_list = []
                interest_list.append(cond_time_max(df=file_df_paf, label=a, threshold=dataset[b], time_maxi=time_max,
                                                   raster_cho=raster_cho, name=name, greater=True))
                for results in interest_list:
                    time_point = results[name, 'time_point [s]']
                    time_length = results[name, 'time_length [s]']
                    for i in range(time_point.shape[0]):
                        if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i]) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                ((file_df_paf['Vbx_sfty_cf_tqi_int_dif'] != 1) |
                                (file_df_paf['Vsx_sfty_esti_tqi_vld'] != 'Nsx_vld_nok_0'))].empty:
                            results.drop([i], axis=0, inplace=True)
                result_list.extend(interest_list)


                # TEST 4
                time_max = 0.5
                rango = 0.01 / 100 * file_df_paf['Vxx_lvl2_tqi_sp_thd']
                a = 'Vxx_lvl1_sfty_tqi_sp'
                c = 'Vxx_lvl2_tqi_sp_thd'
                name = 'Test 4 ' + a
                interest_list = []
                interest_list.append(cond_time_max(df=file_df_paf, label=a, threshold=c, time_maxi=time_max,
                                                 raster_cho=raster_cho, name=name, greater=True, var_compar=True))
                for results in interest_list:
                    time_point = results[name, 'time_point [s]']
                    time_length = results[name, 'time_length [s]']
                    for i in range(time_point.shape[0]):
                        if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i]) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vbx_df_sfty_tq_cmp'] != 1)
                        ].empty:
                            results.drop([i], axis=0, inplace=True)
                        if file_df_paf['timestamps'].loc[
                            (file_df_paf['timestamps'] > time_point[i]) &
                            (file_df_paf['timestamps'] < time_point[i] + time_max) &
                            ((file_df_paf['Vxx_tqi_sp'] < file_df_paf['Vxx_lvl2_tqi_sp_thd'] - rango) &
                            (file_df_paf['Vxx_tqi_sp'] > file_df_paf['Vxx_lvl2_tqi_sp_thd'] + rango))
                        ].empty:
                            results.drop([i], axis=0, inplace=True)
                result_list.extend(interest_list)

                # TEST 5
                time_max = 0
                delay_1 = 0.2
                delay_2 = 0.5
                rango = 0.01 / 100 * file_df_paf['Vxx_sfty_arb_no_agb_tqe']
                a = "Vxx_arb_no_agb_tqe"
                b = "Vxx_sfty_arb_no_agb_tqe"
                c = "_Cmp_sfty_arb_no_agb_ofs"
                name = 'Test 5 ' + '(' + a + ' - ' + b + ')'
                interest_list = []
                interest_list.append(cond_diff_time_max(df=file_df_paf, label1=a, label2=b, threshold=c, time_maxi=time_max,
                                                        raster_cho=raster_cho, name=name, greater=True, var_compar=True))
                for results in interest_list:
                    time_point = results[name, 'time_point [s]']
                    time_length = results[name, 'time_length [s]']
                    if c1a == "Other":
                        for i in range(time_point.shape[0]):
                            if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + delay_1) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                ((file_df_paf['Vxx_arb_no_agb_tqe_can_sfty'] < file_df_paf['Vxx_sfty_arb_no_agb_tqe'] - rango) &
                                 (file_df_paf['Vxx_arb_no_agb_tqe_can_sfty'] > file_df_paf['Vxx_sfty_arb_no_agb_tqe'] + rango))
                            ].empty:
                                results.drop([i], axis=0, inplace=True)
                            elif file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + delay_2) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vbx_df_arb_no_agb_mux_chr'] != 1)].empty:
                                results.drop([i], axis=0, inplace=True)
                    elif c1a == "C1A":
                        for i in range(time_point.shape[0]):
                            if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + delay_1) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                ((file_df_paf['Vxx_sfty_arb_no_agb_tqe_lvl2_chk'] < file_df_paf[
                                    'Vxx_sfty_arb_no_agb_tqe'] - rango) &
                                 (file_df_paf['Vxx_sfty_arb_no_agb_tqe_lvl2_chk'] > file_df_paf[
                                     'Vxx_sfty_arb_no_agb_tqe'] + rango))
                            ].empty:
                                results.drop([i],axis=0, inplace=True)
                result_list.extend(interest_list)

                # TEST 6
                if c1a == "C1A":
                    time_max = 0
                    rango = 0.01 / 100 * file_df_paf['Vxx_sfty_crk_esti_tqe']
                    a = "Vxx_sfty_crk_esti_tqe"
                    b = "Vxx_esti_tqe_wit_dly"
                    c = "_Cmp_sfty_mux_esti_tqe_ofs"
                    delay_1 = 0.2
                    name = 'Test 6' + '|' + a + '-' + b + '|'
                    interest_list = []
                    interest_list.append(cond_diff_abs_time_max(df=file_df_paf, label1=a, label2=b, threshold=c, time_maxi=time_max,
                                                                raster_cho=raster_cho, name=name, greater=True, var_compar=True))
                    for results in interest_list:
                        time_point = results[name, 'time_point [s]']
                        time_length = results[name, 'time_length [s]']
                        for i in range(time_point.shape[0]):
                            if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + delay_1) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                ((file_df_paf['Vxx_sfty_esti_tqe_lvl2_chk'] < file_df_paf[
                                    'Vxx_sfty_crk_esti_tqe'] - rango) &
                                 (file_df_paf['Vxx_sfty_esti_tqe_lvl2_chk'] > file_df_paf[
                                     'Vxx_sfty_crk_esti_tqe'] + rango))
                            ].empty:
                                results.drop([i], axis=0, inplace=True)
                    result_list.extend(interest_list)

                    time_max = 0
                    rango = 0.01 / 100 * file_df_paf['Vxx_sfty_esti_whl_tqe']
                    a = 'Vxx_esti_whl_tqe'
                    b = 'Vxx_sfty_esti_whl_tqe'
                    c = '_Cmp_sfty_mux_esti_whl_tqe_ofs'
                    name = 'Test 6' + '(' + a + '-' + b + ')'
                    interest_list = []
                    interest_list.append(cond_diff_time_max(df=file_df_paf, label1=a, label2=b, threshold=c, time_maxi=time_max,
                                                            raster_cho=raster_cho, name=name, greater=True, var_compar=True))
                    for results in interest_list:
                        time_point = results[name, 'time_point [s]']
                        time_length = results[name, 'time_length [s]']
                        for i in range(time_point.shape[0]):
                            if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i]) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                ((file_df_paf['Vxx_sfty_esti_whl_tqe_lvl2_chk'] < file_df_paf[
                                    'Vxx_sfty_esti_whl_tqe'] - rango) &
                                 (file_df_paf['Vxx_sfty_esti_whl_tqe_lvl2_chk'] > file_df_paf[
                                     'Vxx_sfty_esti_whl_tqe'] + rango))
                            ].empty:
                                results.drop([i], axis=0, inplace=True)
                    result_list.extend(interest_list)
                    interest_list = []
                    interest_list.append(
                        cond_diff_time_max(df=file_df_paf, label1=a, label2=b, threshold=c, time_maxi=time_max,
                                           raster_cho=raster_cho, name=name, greater=False, var_compar=True))

                    rango = 0.01 / 100 * file_df_paf['Vxx_esti_whl_tqe']
                    for results in interest_list:
                        time_point = results[name, 'time_point [s]']
                        time_length = results[name, 'time_length [s]']
                        for i in range(time_point.shape[0]):
                            if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i]) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                ((file_df_paf['Vxx_sfty_esti_tqe_lvl2_chk'] < file_df_paf[
                                    'Vxx_esti_whl_tqe'] - rango) &
                                 (file_df_paf['Vxx_sfty_esti_tqe_lvl2_chk'] > file_df_paf[
                                     'Vxx_esti_whl_tqe'] + rango))
                            ].empty:
                                results.drop([i], axis=0, inplace=True)
                    result_list.extend(interest_list)
                elif c1a == "Other":
                    a = 'Vxx_sfty_dif_abv_esti_tqe'
                    b = 'Vxx_sfty_esti_tqe_ofs'
                    name = 'Test 6 ' + a
                    time_max = 0
                    delay_1 = 0.2
                    delay_2 = 0.5
                    rango = 0.01 / 100 * file_df_paf['Vxx_sfty_esti_tqe']
                    interest_list = []
                    interest_list.append(cond_time_max(df=file_df_paf, label=a, threshold=b, time_maxi=time_max,
                                                       raster_cho=raster_cho,name=name ,greater=True, var_compar=True))
                    for results in interest_list:
                        time_point = results[name, 'time_point [s]']
                        time_length = results[name, 'time_length [s]']
                        for i in range(time_point.shape[0]):
                            if file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i]) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vbx_sfty_df_esti_tqe_req'] != 1)
                            ].empty:
                                results.drop([i], axis=0, inplace=True)
                            elif file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + delay_1) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                ((file_df_paf['Vxx_esti_tqe_can_sfty'] < file_df_paf[
                                    'Vxx_sfty_esti_tqe'] - rango) &
                                 (file_df_paf['Vxx_esti_tqe_can_sfty'] > file_df_paf[
                                     'Vxx_sfty_esti_tqe'] + rango))
                            ].empty:
                                results.drop([i], axis=0, inplace=True)
                            elif file_df_paf['timestamps'].loc[
                                (file_df_paf['timestamps'] > time_point[i] + delay_2) &
                                (file_df_paf['timestamps'] < time_point[i] + time_length[i]) &
                                (file_df_paf['Vbx_df_tqe_mux_chr'] != 1)
                            ].empty:
                                results.drop([i], axis=0, inplace=True)
                    result_list.extend(interest_list)

                # TEST 7
                time_max = 2.2
                t_inc = 0.04
                a = "Vxx_lvl1_sfty_tqi_sp"
                b = "Vxx_sfty_tqi_sp"
                c = "_Ctp_sfty_tqi_rec_pos_err"
                name = 'Test 7 ' + '('+a+' - '+b+')'
                interest_list = []
                interest_list.append(cond_diff_time_max(df=file_df_paf, label1=a, label2=b, threshold=c, time_maxi=time_max,
                                                            raster_cho=raster_cho, name=name, greater=True, var_compar=True))
                for results in interest_list:
                    time_point = results[name, 'time_point [s]']
                    time_length = results[name, 'time_length [s]']
                    for i in range(time_point.shape[0]):
                        points_interest = file_df_paf['Vxx_sfty_tqi_sp_ctr_2'].loc[
                            (file_df_paf['timestamps'] > time_point[i]) &
                            (file_df_paf['timestamps'] < time_point[i] + time_length[i])
                        ]
                        theor_inc = time_length[i] / t_inc
                        real_inc = points_interest.iloc[-1] - points_interest.iloc[0]
                        dif = abs(real_inc - theor_inc)
                        if dif < theor_inc * 2/100:
                            results.drop([i], axis=0, inplace=True)
                result_list.extend(interest_list)

                # TEST 8
                time_max = 2.2
                a = "Vxx_sfty_esti_err_max"
                b = "Vxx_tqi_esti_sp_dif"
                c = "Cxx_sfty_esti_tqi_pos_err_ofs_2"
                interest_list = []
                name = 'Test 8 ' + '(' + a + ' - ' + b + ')'
                interest_list.append(cond_diff_time_max(df=file_df_paf, label1=a, label2=b, threshold=dataset[c], time_maxi=time_max,
                                                        raster_cho=raster_cho, name=name, greater=False))
                for results in interest_list:
                    time_point = results[name, 'time_point [s]']
                    time_length = results[name, 'time_length [s]']
                    for i in range(time_point.shape[0]):
                        points_interest = file_df_paf['Vxx_sfty_esti_tqi_ctr_2'].loc[
                            (file_df_paf['timestamps'] > time_point[i]) &
                            (file_df_paf['timestamps'] < time_point[i] + time_length[i])
                            ]
                        theor_inc = time_length[i] / t_inc
                        real_inc = points_interest.iloc[-1] - points_interest.iloc[0]
                        dif = abs(real_inc - theor_inc)
                        if dif < theor_inc * 2 / 100:
                            results.drop([i], axis=0, inplace=True)
                result_list.extend(interest_list)

                result_list.insert(0,result_inc)
                save_name = tk.filedialog.asksaveasfilename(parent=root,title="Save Report As", defaultextension='.xlsx',
                                                                    initialfile="perf_v2",filetypes=[("Excel files", ".xlsx")])
                with pd.ExcelWriter(save_name, engine="xlsxwriter") as excelwriter:
                    workbook = excelwriter.book
                    number_format = workbook.add_format({'num_format':'# ##0.00'})
                    c = 0
                    for i in result_list:
                        if c == 0:
                            i.to_excel(excelwriter, startcol=c, freeze_panes=(2,0), sheet_name="Perfo_v2")
                            excelwriter.sheets["Perfo_v2"].set_column(0,0,36)
                            excelwriter.sheets["Perfo_v2"].set_column(1,len(i.columns),20,number_format)
                        else:
                            i.to_excel(excelwriter, startcol=c, freeze_panes=(2,0), sheet_name="Perfo_v2")
                            excelwriter.sheets["Perfo_v2"].set_column(c+1, c+len(i.columns),15,number_format)
                        c += len(i.columns) + 2
                    excelwriter.save()
                    wait_label.destroy()
                    excelwriter.close()
                    w = 175
                    h = 75
                    ws = root.winfo_screenwidth()
                    hs = root.winfo_screenheight()
                    x = (ws / 2) - (w / 2)
                    y = (hs / 2) - (h / 2)
                    root2 = tk.Toplevel()
                    root2.geometry("%dx%d+%d+%d" % (w, h, x, y))
                    frame_new = tk.Frame(root2)
                    frame_new.pack(expand=True, fill="both")
                    message_finish = tk.Label(frame_new, text="Done!", font='Helvetica 18 bold')
                    message_finish.config(fg='#14890a', anchor="n")
                    message_finish.pack(side="top", fill="x")
                    button_finish = tk.Button(frame_new, text="OK", width=10, command=root2.destroy, bd=5)
                    button_finish.pack(pady=5, side="bottom")
                    frame_new.grab_set()
                    root2.mainloop()
            except:
                wait_label.destroy()
                w = 200
                h = 100
                ws = root.winfo_screenwidth()
                hs = root.winfo_screenheight()
                x = (ws / 2) - (w / 2)
                y = (hs / 2) - (h / 2)
                root2 = tk.Toplevel()
                root2.geometry("%dx%d+%d+%d" % (w, h, x, y))
                frame_new = tk.Frame(root2)
                frame_new.pack(expand=True, fill="both")
                message_finish = tk.Label(frame_new, text="Oops!\n Something went wrong.", font='Helvetica 12 bold')
                message_finish.config(fg='#d60606', anchor="n")
                message_finish.pack(side="top", fill="x")
                button_finish = tk.Button(frame_new, text="OK", width=10, command=root2.destroy, bd=5)
                button_finish.pack(pady=5, side="bottom")
                frame_new.grab_set()
                root2.mainloop()

    except:
        wait_label.destroy()
        w=200
        h=100
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        root2=tk.Toplevel()
        root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
        frame_new=tk.Frame(root2)
        frame_new.pack(expand=True,fill="both")
        message_finish=tk.Label(frame_new,text="Oops!\n Something went wrong.",font='Helvetica 12 bold')
        message_finish.config(fg='#d60606',anchor="n")
        message_finish.pack(side="top",fill="x")
        button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
        button_finish.pack(pady=5,side="bottom")
        frame_new.grab_set()
        root2.mainloop()
        pass


def perf_v3_v4 (root, labels, raster_cho, dataset, c1a):
    try:
        wait_label=tk.Label(root,text="PROCESSING...PLEASE WAIT",height=5,width=30)
        wait_label.config(fg="#2330e1")
        wait_label.pack(side="bottom", fill="x")
        file_df=to_pd (root, raster_cho, labels)
        file_df_diag_ena=file_df.loc[((file_df["Vxx_sfty_n"]>dataset["Cxx_sfty_diag_ena_n_thd"])&
                                      (file_df["Vbx_sfty_eng_aut"]==1)&
                                      (file_df["Vxx_sfty_vs"]>dataset["Cxx_sfty_vs_dsb_vs_thd"])),:].copy()
        result_inc=pd.DataFrame()
        result_list=[]
        labels_inc=["Vxx_sfty_tqi_sp_ctr_2","Vxx_sfty_esti_tqi_ctr_2","Vsx_sfty_esti_tqi_vld"]
        for i in labels_inc:
            result_inc = pd.concat([result_inc, increments(df=file_df,label=i)], axis=1, join="outer")
        time_maxi=0.2
        labels_diff_abs_time_max=[["Vxx_lvl1_sfty_tqi_sp_40ms","Vxx_sfty_tqi_sp","Cmp_sfty_tqi_req_pos_err"],
                                  ["Vxx_lvl1_sfty_tqi_sp","Vxx_sfty_tqi_sp","Cmp_sfty_tqi_req_pos_err"],
                                  ["Vxx_arb_no_agb_tqe","Vxx_sfty_arb_no_agb_tqe","Cmp_sfty_tqi_req_pos_err"],
                                  ["Vxx_driv_pwt_sp_wo_dly","Vxx_sfty_driv_adas_pwt_sp","Cxx_sfty_mux_driv_pwt_sp_ofs"]]
        for a,b,c in labels_diff_abs_time_max:
            result_list.append(cond_diff_abs_time_max(df=file_df_diag_ena,label1=a,label2=b,threshold=dataset[c]/2,
                                                      time_maxi=time_maxi,raster_cho=raster_cho,name=str("| "+a+" - "+b+" |")))
        if c1a=="C1A":
            a="Vxx_sfty_crk_esti_tqe"
            b="Vxx_esti_tqe_wit_dly"
            c="Cmp_sfty_tqi_req_pos_err"
            result_list.append(cond_diff_abs_time_max(df=file_df_diag_ena,label1=a,label2=b,threshold=dataset[c]/2,
                                                      time_maxi=time_maxi,raster_cho=raster_cho,name=str("| "+a+" - "+b+" |")))
        time_maxi=0.2
        labels_abs_time_max=[["Vxx_sfty_tqi_esti_sp_dif","Cmp_sfty_tqi_req_pos_err"]]
        for a,c in labels_abs_time_max:
            result_list.append(cond_abs_time_max (df=file_df_diag_ena,label=a, threshold=dataset[c]/2, time_maxi=time_maxi,
                                                  raster_cho=raster_cho, name=str("| "+a+" |")))
        time_maxi=0
        labels_diff_time_max=[["Vxx_sfty_tco_mdl","Vxx_tco","Seuil_PERFO_v3"]]
        for a,b,c in labels_diff_time_max:
            result_list.append(cond_diff_time_max(df=file_df_diag_ena,label1=a,label2=b,threshold=dataset[c]/2,
                                                  time_maxi=time_maxi,raster_cho=raster_cho,name=str(a+" - "+b)))
        time_maxi=0.2
        if c1a=="Other":
            a="Vxx_sfty_dif_abv_esti_tqe"
            c="Cmp_sfty_tqi_req_pos_err"
            result_list.append(cond_time_max (df=file_df_diag_ena,label=a, threshold=dataset[c]/2, time_maxi=time_maxi,
                                              raster_cho=raster_cho, name=str(a)))
        result_list.insert(0,result_inc)
        try:
            save_name=tk.filedialog.asksaveasfilename(parent=root,title="Save Report As",defaultextension='.xlsx',
                                                      initialfile="perf_v3_v4",filetypes=[("Excel files", ".xlsx")])
            excelwriter = pd.ExcelWriter(save_name,engine="xlsxwriter")
            workbook=excelwriter.book
            number_format=workbook.add_format({'num_format':'# ##0.00'})
            c=0
            for i in result_list:
                if c==0:
                    i.to_excel(excelwriter,startcol=c,freeze_panes=(2,0),sheet_name="PERFO_v3_v4")
                    excelwriter.sheets["PERFO_v3_v4"].set_column(0,0,36)
                    excelwriter.sheets["PERFO_v3_v4"].set_column(1,len(i.columns),20,number_format)
                else:
                    i.to_excel(excelwriter,startcol=c,freeze_panes=(2,0),sheet_name="PERFO_v3_v4")
                    excelwriter.sheets["PERFO_v3_v4"].set_column(c+1,c+len(i.columns),15,number_format)
                c+=(len(i.columns)+2)
            excelwriter.save()
            wait_label.destroy()
            excelwriter.close()
            w=175
            h=75
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root2=tk.Toplevel()
            root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
            frame_new=tk.Frame(root2)
            frame_new.pack(expand=True,fill="both")
            message_finish=tk.Label(frame_new,text="Done!",font='Helvetica 18 bold')
            message_finish.config(fg='#14890a',anchor="n")
            message_finish.pack(side="top",fill="x")
            button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
            button_finish.pack(pady=5,side="bottom")
            frame_new.grab_set()
            root2.mainloop()
        except:
            wait_label.destroy()
            w=200
            h=100
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            x = (ws/2) - (w/2)
            y = (hs/2) - (h/2)
            root2=tk.Toplevel()
            root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
            frame_new=tk.Frame(root2)
            frame_new.pack(expand=True,fill="both")
            message_finish=tk.Label(frame_new,text="Oops!\n Something went wrong.",font='Helvetica 12 bold')
            message_finish.config(fg='#d60606',anchor="n")
            message_finish.pack(side="top",fill="x")
            button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
            button_finish.pack(pady=5,side="bottom")
            frame_new.grab_set()
            root2.mainloop()
            pass
    except:
        wait_label.destroy()
        w=200
        h=100
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        root2=tk.Toplevel()
        root2.geometry("%dx%d+%d+%d" % (w,h,x, y))
        frame_new=tk.Frame(root2)
        frame_new.pack(expand=True,fill="both")
        message_finish=tk.Label(frame_new,text="Oops!\n Something went wrong.",font='Helvetica 12 bold')
        message_finish.config(fg='#d60606',anchor="n")
        message_finish.pack(side="top",fill="x")
        button_finish=tk.Button(frame_new, text="OK", width=10,command=root2.destroy,bd=5)
        button_finish.pack(pady=5,side="bottom")
        frame_new.grab_set()
        root2.mainloop()
        pass


def gui_configuration():
    thresholds_list = ["Cxx_sfty_diag_ena_n_thd", "Cxx_sfty_vs_dsb_vs_thd", "Cmp_sfty_tqi_req_pos_err",
                       "Cmp_tqi_sp_sfty_ofs", "Cxx_sfty_dif_max_tqe_err", "Cxx_sfty_dif_min_driv_err",
                       "Cxx_sfty_eng_tql_chr_thd", "Seuil_%_AGR_v1",
                       "Seuil_Nm_AGR_v1", "Seuil_W_AGR_v1", "Cxx_sfty_mux_driv_pwt_sp_ofs",
                       "Ecart_main_inj_PERFO_v2 [mg/cp]", "Ecart_tot_inj_PERFO_v2 [mg/cp]", "Ecart_pinj_PERFO_v2 [mg/cp]",
                       "Seuil_Nms_PERFO_v2","Cxx_sfty_esti_tqi_pos_err_ofs_2","Cxx_sfty_tqi_int_tol"]

    entry_dict={}
    thresholds_dict={}
    root=tk.Tk()
    canvas = tk.Canvas(root)
    w = 600
    h = 640
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.title("VALIDATION TQMON TOOL v1.6")
    root.geometry("%dx%d+%d+%d" % (w,h,x, y))
    root.minsize(w,h)
    root.maxsize(w,h)
    frame_main=tk.Frame(root)
    frame_main.pack(expand=True,fill="both")
    frame_lvl1=tk.Frame(frame_main)
    frame_lvl1.pack(side="top",fill="x")
    frame_lvl2=tk.Frame(frame_main)
    frame_lvl2.pack(side="top",expand=True,pady=1)
    frame_lvl3=tk.Frame(frame_main)
    frame_lvl3.pack(side="top",pady=5)
    frame_lvl4=tk.Frame(frame_main)
    frame_lvl4.pack(side="right")
    alert_label=tk.Label(frame_lvl1,text="")
    alert_label.config(fg='#ff1b1b',anchor="n")
    alert_label.pack(side="top",fill="x")
    m_main=tk.PanedWindow(frame_lvl2,orient = "vertical")
    m_main.pack(fill="both",expand=True)
    m1=tk.PanedWindow(m_main,orient = "horizontal")
    m_main.add(m1)
    config_message=tk.Label(m1,text="Tool's configuration")
    config_message.pack(ipadx=10, ipady=10,pady=10,fill="x")
    config_message.config(bg='lightblue',anchor="center")
    m1=tk.PanedWindow(m_main,orient = "horizontal")
    m_main.add(m1)
    label_engine=tk.Label(m1,text="Engine type : ",height=2,width=40)
    label_engine.config(anchor="e")
    m1.add(label_engine)
    engine_type=Listbox_enginetype(m1)
    m1.add(engine_type)
    m1=tk.PanedWindow(m_main,orient = "horizontal")
    m_main.add(m1)
    label_c1a=tk.Label(m1,text="Electronic architecture : ",height=2,width=40)
    label_c1a.config(anchor="e")
    m1.add(label_c1a)
    c1a_type=Listbox_c1a(m1)
    m1.add(c1a_type)
    m1=tk.PanedWindow(m_main,orient = "horizontal")
    m_main.add(m1)
    label_raster=tk.Label(m1,text="Resampling time [s] (recommended ≤ 0.02s): ",height=1,width=40)
    label_raster.config(anchor="e")
    m1.add(label_raster)
    entry_raster=Entryreturnvalue(m1)
    m1.add(entry_raster)
    m2=tk.PanedWindow(m_main,orient = "horizontal")
    m_main.add(m2)
    threshold_message=tk.Label(m2,text="Validation thresholds")
    threshold_message.pack(ipadx=10, ipady=10,pady=10,fill="x")
    threshold_message.config(bg='lightblue',anchor="center")
    m3 = tk.PanedWindow(m_main, orient="horizontal")
    m_main.add(m3)
    setpoint_message=tk.Label(m3,text="SETPOINT (AGR)")
    setpoint_message.grid(row=2,column=0,ipadx=50,pady=5)
    setpoint_message.config(bg='pale turquoise')
    esti_message=tk.Label(m3,text="ESTI (PERFO)")
    esti_message.grid(row=2,column=1,columnspan=2,pady=5, ipadx=30)
    esti_message.config(bg='pale turquoise')
    canvas.create_rectangle(50,100,100,200,fill='pale turquoise')
    canvas.pack(fill=tk.BOTH, expand=1)
    m4 = tk.PanedWindow(m_main,orient="horizontal")
    m_main.add(m4)
    diesel_label = tk.Label(m4,text='Diesel')
    diesel_label.config(bg='cyan')
    diesel_label.grid(row=2,column=2,columnspan=2,ipadx=115)
    gasoline_label = tk.Label(m4,text='Gasoline')
    gasoline_label.config(bg='cyan')
    gasoline_label.grid(row=8,column=2,columnspan=2, ipadx=110)
    for i,threshold in enumerate(thresholds_list[0:2]): # COMMON LABELS
        label = tk.Label(m3, text=threshold+" : ",height=1,width=30,anchor='e',padx=70).grid(row=i)
        entry = Entryreturnvalue(m3, row=i,column=1)
        entry_dict[threshold] = entry
    m3.grid_rowconfigure(0, minsize=30)
    for i,threshold in enumerate(thresholds_list[2:10]): # AGR LABELS
        label = tk.Label(m4,text=threshold+" : ",height=1,width=30, anchor='e').grid(row=i+2,column=0)
        entry = Entryreturnvalue(m4,row=i+2,column=1)
        entry_dict[threshold] = entry
    for i,threshold in enumerate(thresholds_list[10:15]): #PERFO DIESEL LABELS
        label = tk.Label(m4,text=threshold+" : ",height=1, width=30, anchor='e').grid(row=i+3,column=2)
        entry = Entryreturnvalue(m4,row=i+3,column=3)
        entry_dict[threshold] = entry
    for i,threshold in enumerate(thresholds_list[15:]): # PERFO GASOLINE LABELS
        label = tk.Label(m4,text=threshold+" : ",height=1, width=30, anchor='e').grid(row=i+9,column=2)
        entry = Entryreturnvalue(m4,row=i+9,column=3)
        entry_dict[threshold] = entry

    button1=tk.Button(frame_lvl3, text="Save", width=15, command=lambda:save_button(root,entry_dict,engine_type,
                                                                                    alert_label,entry_raster,c1a_type), bd=5)
    button1.pack(ipadx=1, ipady=10,side="left")
    email_label=tk.Label(frame_lvl4,text="hector.garcia-carton@renault.com")
    email_label.config(fg='#2330e1',anchor="se")
    email_label.pack(side="bottom")
    root.mainloop()
    engine_choice=engine_type.value
    c1a_choice=c1a_type.value
    raster_cho=float(entry_raster.valuereturn())
    for i in thresholds_list:
        thresholds_dict[i]=float(entry_dict[i].valuereturn())
    thresholds_dict["Cxx_sfty_mux_driv_pwt_sp_ofs"]=thresholds_dict["Cxx_sfty_mux_driv_pwt_sp_ofs"]*2
    thresholds_dict["Seuil_%_AGR_v1"]=thresholds_dict["Seuil_%_AGR_v1"]/100
    thresholds_dict["Seuil_W_AGR_v1"]=thresholds_dict["Seuil_W_AGR_v1"]*2
    thresholds_dict["Seuil_Nm_AGR_v1"]=thresholds_dict["Seuil_Nm_AGR_v1"]*2
    thresholds_dict["Seuil_PERFO_v3"]=0
    thresholds_dict["Seuil_Nms_PERFO_v2"]=thresholds_dict["Seuil_Nms_PERFO_v2"]*2
    thresholds_dict["Ecart_pinj_PERFO_v2 [mg/cp]"]=thresholds_dict["Ecart_pinj_PERFO_v2 [mg/cp]"]*2
    thresholds_dict["Ecart_main_inj_PERFO_v2 [mg/cp]"]=thresholds_dict["Ecart_main_inj_PERFO_v2 [mg/cp]"]*2
    thresholds_dict["Ecart_tot_inj_PERFO_v2 [mg/cp]"]=thresholds_dict["Ecart_tot_inj_PERFO_v2 [mg/cp]"]*2
    return thresholds_dict, engine_choice, raster_cho, c1a_choice


def save_button (root,entry_dict,engine_type,alert_label,entry_raster,c1a_type):
    message= tk.StringVar()
    try:
        engine_type.valuereturn()
        c1a_type.valuereturn()
        configuration_dict={}
        thresholds_dict={}
        configuration_dict["engine type"]=engine_type.value
        configuration_dict["c1a type"]=c1a_type.value
        configuration_dict["raster"]=entry_raster.valuereturn()
        for i in entry_dict:
            thresholds_dict[i]=(entry_dict[i].valuereturn())
        if (all (value != "" for value in thresholds_dict.values())) and (all (value != "" for value in configuration_dict.values())):
                root.destroy()
        elif (all (value != "" for value in configuration_dict.values())):
            message.set("Fill all values in 'Validation's thresholds'")
            alert_label.config(textvariable=message)
        elif (any (value == "" for value in thresholds_dict.values())) and (any (value == "" for value in configuration_dict.values())):
            message.set("Fill all values in 'Validation's thresholds' and 'Tool's configuration'")
            alert_label.config(textvariable=message)
        elif (any (value == "" for value in configuration_dict.values())):
            message.set("Fill all values in 'Tool's configuration'")
            alert_label.config(textvariable=message)
    except:
        thresholds_dict={}
        for i in entry_dict:
            thresholds_dict[i]=(entry_dict[i].valuereturn())
        if any (value == "" for value in thresholds_dict.values()):
            message.set("Fill all values in 'Validation's thresholds' and 'Tool's configuration'")
            alert_label.config(textvariable=message)
        else:
            message.set("Fill all values in 'Tool's configuration'")
            alert_label.config(textvariable=message)


def gui_validation_selection(thresholds_dict,engine_choice,raster_cho,c1a_choice):
    if engine_choice=="K9K Gen8 Full":
        labels =["Vxx_arb_no_agb_tqe","Vxx_sfty_arb_no_agb_tqe","Vxx_sfty_tqi_sp_ctr_2","Vxx_sfty_esti_tqi_ctr_2",
                 "Vsx_sfty_esti_tqi_vld","Vsx_sfty_eng_tql_vld","Vsx_sfty_min_driv_tqe_vld","Vsx_sfty_max_tqe_vld",
                 "Vsx_sfty_is_req_vld","Vxx_sfty_tqi_sp","Vxx_lvl1_sfty_tqi_sp_40ms","Vxx_lvl2_tqi_sp_thd",
                 "Vxx_lvl1_sfty_tqi_sp","Vxx_eng_tql","Vxx_sfty_eng_tql","Vxx_sfty_max_tqe","Vxx_max_stat_avl_tqe",
                 "Vxx_max_dyn_avl_tqe","Vxx_min_avl_tqe","Vxx_min_driv_tqe","Vxx_sfty_min_driv_tqe","Vxx_sfty_tqi_esti_sp_dif",
                 "Vxx_sfty_crk_esti_tqe","Vxx_esti_tqe_wit_dly","Vxx_sfty_dif_abv_esti_tqe","Vxx_sfty_max_eco_tqe",
                 "Vxx_sfty_tkof_tqe_cor","Vxx_tkof_tqe_cor","Vxx_sfty_lim_driv_tqe_sp","Vxx_lim_driv_tqe_sp",
                 "Vxx_sfty_ajs_modu_tqe","Vxx_ajs_modu_tqe_sp","Vxx_sfty_ajs_cor_dyn_tqe","Vxx_ajs_cor_dyn_tqe",
                 "Vxx_sfty_arb_tqe","Vxx_arb_tqe_sp","Vxx_sfty_is_tqe_sp","Vxx_is_tqe_sp","Vxx_sfty_ac_pow_max","Vxx_ac_pow",
                 "Vxx_sfty_alt_pow_max","Vxx_fil_alt_pow","Vxx_sfty_n","Vbx_sfty_eng_aut","Vxx_sfty_vs","Vxx_sfty_acel_pdl_fmt_fac",
                 "Vxx_acel_pdl_fmt_fac","Vxx_sfty_acel_pdl_fmt_fac_eco","Vxx_acel_pdl_fmt_fac_eco","Vxx_sfty_acel_pdl_fmt_fac_off_road",
                 "Vxx_acel_pdl_fmt_fac_off_road","Vxx_sfty_acel_pdl_fmt_fac_snw","Vxx_acel_pdl_fmt_fac_snw",
                 "Vxx_sfty_acel_pdl_fmt_fac_spt","Vxx_acel_pdl_fmt_fac_spt","Vxx_sfty_acel_pdl_pwt_sp","Vxx_acel_pdl_pwt_sp",
                 "Vxx_sfty_driv_pwt_sp","Vxx_driv_pwt_sp","Vxx_tqi_sp","Vxx_sfty_tqi_sp","Vxx_driv_pwt_sp_wo_dly",
                 "Vxx_sfty_driv_adas_pwt_sp","Vxx_tco","Vxx_sfty_tco_mdl","Vxx_acel_pdl_rat","Vnx_cmb_param_set_crt",
                 "Vxx_fms_fim_main","Vxx_sfty_fms_fim_main","Vxx_fms_faf","Vxx_sfty_fms_faf","Vxx_fms_fpo","Vxx_sfty_fms_fpo",
                 "Vxx_fms_fp1","Vxx_sfty_fms_fp4","Vxx_fms_fp2","Vxx_sfty_fms_fp3","Vxx_tqi_fim_tot","Vxx_sfty_fms_tot_efy",
                 "Vxx_fms_fim_tot","Vxx_sfty_tqi_int_err"]
    if engine_choice == 'Gasoline':
        labels = ["Vxx_arb_no_agb_tqe","Vxx_sfty_arb_no_agb_tqe","Vxx_sfty_tqi_sp_ctr_2","Vxx_sfty_esti_tqi_ctr_2",
                 "Vsx_sfty_esti_tqi_vld","Vsx_sfty_eng_tql_vld","Vsx_sfty_min_driv_tqe_vld","Vsx_sfty_max_tqe_vld",
                 "Vsx_sfty_is_req_vld","Vxx_sfty_tqi_sp","Vxx_lvl1_sfty_tqi_sp_40ms","Vxx_lvl2_tqi_sp_thd",
                 "Vxx_lvl1_sfty_tqi_sp","Vxx_eng_tql","Vxx_sfty_eng_tql","Vxx_max_stat_avl_tqe","Vxx_acel_pdl_fmt_fac_off_road",
                 "Vxx_max_dyn_avl_tqe","Vxx_min_avl_tqe","Vxx_min_driv_tqe","Vxx_sfty_tqi_esti_sp_dif",
                 "Vxx_sfty_crk_esti_tqe","Vxx_esti_tqe_wit_dly","Vxx_sfty_dif_abv_esti_tqe","Vxx_sfty_max_eco_tqe",
                 "Vxx_sfty_tkof_tqe_cor","Vxx_tkof_tqe_cor","Vxx_sfty_lim_driv_tqe_sp","Vxx_lim_driv_tqe_sp",
                 "Vxx_sfty_ajs_modu_tqe","Vxx_ajs_modu_tqe_sp","Vxx_sfty_ajs_cor_dyn_tqe","Vxx_ajs_cor_dyn_tqe",
                 "Vxx_sfty_arb_tqe","Vxx_arb_tqe_sp","Vxx_sfty_is_tqe_sp","Vxx_is_tqe_sp","Vxx_sfty_ac_pow_max","Vxx_ac_pow",
                 "Vxx_sfty_alt_pow_max","Vxx_fil_alt_pow","Vxx_sfty_n","Vxx_sfty_vs","Vxx_sfty_acel_pdl_fmt_fac",
                 "Vxx_acel_pdl_fmt_fac","Vxx_sfty_acel_pdl_fmt_fac_eco","Vxx_acel_pdl_fmt_fac_eco",
                 "Vxx_sfty_acel_pdl_fmt_fac_spt","Vxx_acel_pdl_fmt_fac_spt","Vxx_sfty_acel_pdl_pwt_sp","Vxx_acel_pdl_pwt_sp",
                 "Vxx_sfty_driv_pwt_sp","Vxx_driv_pwt_sp","Vxx_tqi_sp","Vxx_driv_pwt_sp_wo_dly", "Vxx_acel_pdl_rat",
                 "Vxx_sfty_driv_adas_pwt_sp","Vxx_tco","Vxx_sfty_tco_mdl", "Vxx_tqi_esti_sp_dif", "Vxx_sfty_esti_whl_tqe",
                 "Vxx_sfty_tqi_int_err","Vbx_sfty_df_tqi_sp_chr","Vxx_esti_whl_tqe",
                 "Vxx_sfty_esti_err_max", 'Vbx_sfty_eng_aut',"Vxx_sfty_acel_pdl_fmt_fac_off_road","Vxx_acel_pdl_fmt_fac_snw",
                 "Vxx_sfty_acel_pdl_fmt_fac_snw","Vxx_sfty_min_driv_tqe","_Cmp_sfty_tqi_rec_pos_err"]
        labels_perf = ["Vxx_arb_no_agb_tqe", "Vxx_sfty_arb_no_agb_tqe", "Vxx_sfty_tqi_sp_ctr_2",
                      "Vxx_sfty_esti_tqi_ctr_2","Vxx_sfty_esti_tqe","Vxx_sfty_esti_tqe_ofs",
                      "Vsx_sfty_esti_tqi_vld", "Vsx_sfty_eng_tql_vld", "Vsx_sfty_min_driv_tqe_vld",
                      "Vsx_sfty_max_tqe_vld", "Vbx_df_arb_no_agb_mux_chr",
                      "Vsx_sfty_is_req_vld", "Vxx_sfty_tqi_sp", "Vxx_lvl1_sfty_tqi_sp_40ms", "Vxx_lvl2_tqi_sp_thd",
                      "Vxx_lvl1_sfty_tqi_sp", "Vxx_eng_tql", "Vxx_sfty_eng_tql", "Vxx_max_stat_avl_tqe",
                      "Vxx_max_dyn_avl_tqe", "Vxx_min_avl_tqe", "Vxx_min_driv_tqe", "Vxx_sfty_tqi_esti_sp_dif",
                      "Vxx_sfty_crk_esti_tqe", "Vxx_esti_tqe_wit_dly", "Vxx_sfty_dif_abv_esti_tqe",
                      "Vxx_sfty_max_eco_tqe", "Vxx_arb_no_agb_tqe_can_sfty",
                      "Vxx_sfty_tkof_tqe_cor", "Vxx_tkof_tqe_cor", "Vxx_sfty_lim_driv_tqe_sp", "Vxx_lim_driv_tqe_sp",
                      "Vxx_sfty_ajs_modu_tqe", "Vxx_ajs_modu_tqe_sp", "Vxx_sfty_ajs_cor_dyn_tqe", "Vxx_ajs_cor_dyn_tqe",
                      "Vxx_sfty_arb_tqe", "Vxx_arb_tqe_sp", "Vxx_sfty_is_tqe_sp", "Vxx_is_tqe_sp",
                      "Vxx_sfty_ac_pow_max", "Vxx_ac_pow", "Vxx_sfty_esti_tqe_lvl2_chk",
                      "Vxx_sfty_alt_pow_max", "Vxx_fil_alt_pow", "Vxx_sfty_n", "Vxx_sfty_vs",
                      "Vxx_sfty_acel_pdl_fmt_fac", "Vxx_sfty_arb_no_agb_tqe_lvl2_chk",
                      "Vxx_acel_pdl_fmt_fac", "Vxx_sfty_acel_pdl_fmt_fac_eco", "Vxx_acel_pdl_fmt_fac_eco",
                      "Vxx_sfty_acel_pdl_fmt_fac_spt", "Vxx_acel_pdl_fmt_fac_spt", "Vxx_sfty_acel_pdl_pwt_sp",
                      "Vxx_acel_pdl_pwt_sp", 'Vbx_df_sfty_tq_cmp', "Vxx_sfty_esti_whl_tqe_lvl2_chk",
                      "Vxx_sfty_driv_pwt_sp", "Vxx_driv_pwt_sp", "Vxx_tqi_sp", "Vxx_driv_pwt_sp_wo_dly",
                      "Vxx_sfty_driv_adas_pwt_sp", "Vxx_tco", "Vxx_sfty_tco_mdl", "Vxx_tqi_esti_sp_dif",
                      "Vxx_sfty_esti_whl_tqe", 'Vbx_sfty_df_esti_tqi_chr',
                      "Vxx_sfty_tqi_int_err", "Vbx_sfty_df_tqi_sp_chr", "Vxx_esti_whl_tqe",
                      "Vxx_sfty_esti_err_max", "_Cmp_sfty_tqi_rec_pos_err", "_Cmp_sfty_mux_esti_tqe_ofs",
                       "_Cmp_sfty_mux_esti_whl_tqe_ofs", "_Ctp_sfty_tqi_rec_pos_err", "_Cmp_sfty_arb_no_agb_ofs"]

    root=tk.Tk()
    w = 450
    h = 350
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.title("VALIDATION TQMON TOOL v1.6")
    root.geometry("%dx%d+%d+%d" % (w,h,x, y))
    root.minsize(w,h)
    root.maxsize(w,h)
    frame_main=tk.Frame(root)
    frame_main.pack(expand=True,fill="both",pady=10)
    frame_lvl1=tk.Frame(frame_main)
    frame_lvl1.pack(side="top",fill="x",expand=True,pady=5)
    frame_lvl2=tk.Frame(frame_main)
    frame_lvl2.pack(side="top",fill="x",expand=True,pady=5)
    frame_lvl3=tk.Frame(frame_main)
    frame_lvl3.pack(side="top",fill="x",expand=True,pady=5)
    frame_lvl4=tk.Frame(frame_main)
    frame_lvl4.pack(side="top",fill="x",expand=True,pady=5)
    frame_lvl5=tk.Frame(frame_main)
    frame_lvl5.pack(side="right")
    button_agr_v1=tk.Button(frame_lvl1, text="Agrément - Step V1 ", width=30,
                            command=lambda:agr_v1(frame_lvl4,labels,raster_cho,thresholds_dict),bd=5)
    button_agr_v2_v3_v5=tk.Button(frame_lvl2, text="Agrément - Steps V2 / V3 / V5 ", width=30,
                                  command=lambda:agr_v2_v3_v5 (frame_lvl4,labels,raster_cho,thresholds_dict,c1a_choice),bd=5)
    if engine_choice == 'K9K Gen8 Full':
        button_perf_v2=tk.Button(frame_lvl3, text="Perfo - Step V2", width=30,
                                command=lambda:perf_v2(frame_lvl4,labels,raster_cho,thresholds_dict,c1a_choice,engine_choice),bd=5)
    elif engine_choice == "Gasoline":
        button_perf_v2 = tk.Button(frame_lvl3, text="Perfo - Step V2", width=30,
                                   command=lambda: perf_v2(frame_lvl4, labels_perf, raster_cho, thresholds_dict, c1a_choice,
                                                           engine_choice), bd=5)
    button_perf_v3_v4=tk.Button(frame_lvl4, text="Perfo - Step V3 / V4", width=30,
                                command=lambda:perf_v3_v4(frame_lvl4,labels, raster_cho,thresholds_dict,c1a_choice),bd=5)
    button_agr_v1.pack(ipadx=1, ipady=10,side="top")
    button_agr_v2_v3_v5.pack(ipadx=1, ipady=10,side="top")
    button_perf_v2.pack(ipadx=1, ipady=10,side="top")
    button_perf_v3_v4.pack(ipadx=1, ipady=10,side="top")
    email_label=tk.Label(frame_lvl5,text="hector.garcia-carton@renault.com")
    email_label.config(fg='#2330e1',anchor="se")
    email_label.pack(side="bottom")
    root.mainloop()


def valid_tqmon_tool ():
    thresholds_dict, engine_choice, raster_cho, c1a_choice = gui_configuration()
    gui_validation_selection(thresholds_dict,engine_choice,raster_cho,c1a_choice)


# In[ ]:


valid_tqmon_tool()

