import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import seaborn as sns
import plotly.express as px
from streamlit_option_menu import option_menu
import openpyxl
import datetime
import time


st.set_page_config(page_title = 'Application')
st.title("Supplier Analysis")

with st.sidebar:
    selected=option_menu(
        menu_title='Main Menu',
        options=["Home"]
    )
    
if selected=='Home':
    file= st.file_uploader(label = 'Upload your dataset:',type=['xlsx','csv'])
    if file is not None:
        @st.cache_data
        def read_data(file):
            po_receiving_data=pd.read_excel(file,na_values='Missing',usecols="C,F,M,O:P",engine='openpyxl')
            st.toast('File upload successfully.', icon="✅")
            time.sleep(6)
            # st.success("Items with no ID are omitted") 
            return po_receiving_data
        po_receiving_data=read_data(file)
        df_main=po_receiving_data.copy()   
        st.title("Data")
        st.write(df_main.sample(7).reset_index(drop=True))
        df_main['ITEM_ID'].fillna(-1,inplace=True)
        if df_main['ITEM_ID'].dtype != 'O':
            df_main['ITEM_ID']=pd.to_numeric(df_main['ITEM_ID'], downcast='integer', errors='coerce') 
        # st.write(df_main.dtypes)
        df_main['TRANSACTION_DATE']=pd.to_datetime(df_main['TRANSACTION_DATE']).dt.normalize().copy()
        acpt_df=df_main.loc[(df_main['TRANSACTION_TYPE']=='ACCEPT') & (df_main['ITEM_ID']!=-1)].copy()
        a=pd.to_datetime(acpt_df['TRANSACTION_DATE'])                                                                               
        acpt_df['TRANSACTION_DATE']=pd.to_datetime(a.dt.strftime("%m-%d-%y")).copy()                                                
        acpt_df.reset_index(drop=True,inplace=True)  
        # st.header("Accepted data")
        # st.write(acpt_df.sample(5).reset_index(drop=True)) 
        acpt_df['MONTH']=acpt_df['TRANSACTION_DATE']
        acpt_df.set_index('MONTH',inplace=True)     
        rej_df = df_main.loc[(df_main['ITEM_ID']!=-1) & ((df_main['TRANSACTION_TYPE']=='REJECT'))].copy()
        rej_df=rej_df.sort_values(by=['TRANSACTION_DATE']).copy()
        rej_df.reset_index(drop=True, inplace=True)
        # st.header("Rejection data")
        # st.write(rej_df.sample(5).reset_index(drop=True))
        # rej_df['REJECTION_RATE']=0.0                                            
        # rej_df.reset_index(drop=True, inplace=True)                                                                                 
        # rej_df['TRANSACTION_TYPE']='REJECT'                                              
        # a=pd.to_datetime(rej_df['TRANSACTION_DATE'],errors='coerce')                                                                                
        # rej_df['TRANSACTION_DATE']=pd.to_datetime(a.dt.strftime("%m-%d-%y")).copy()                                         
        # rej_df.reset_index(drop=True,inplace=True)       
        rej_df['MONTH']=rej_df['TRANSACTION_DATE']                                                                                  
        rej_df.set_index('MONTH',inplace=True)   
        # st.header("Analysis")  
        typ=list(df_main['TRANSACTION_TYPE'].unique())
        qnt=[]
        for i in typ:
            qnt.append(df_main.loc[(df_main['TRANSACTION_TYPE']==i)& (df_main['ITEM_ID']!=-1)]['ACTUAL_QUANTITY'].sum())
        # fig,ax=plt.subplots(figsize=(18,6))
        # plt.bar(typ,qnt)
        # for i ,v in enumerate(qnt):
        #     plt.text(i,v,str(v),ha='center')
        # plt.xlabel("Transaction Type")
        # plt.ylabel("Quantity")
        # st.pyplot(fig)
        # key=['ACCEPTED','REJECTED']
        # values=[]
        # values.append(acpt_df['ACTUAL_QUANTITY'].sum())
        # values.append(rej_df['ACTUAL_QUANTITY'].sum())    
        # fig1, ax1 = plt.subplots(figsize=(10,5))
        # ax1.pie(values,labels=key,autopct="%1.1f%%")
        # ax1.axis('equal')  
        # plt.legend()
        # st.pyplot(fig1)
        # rej=dict(rej_df.groupby(["VENDOR_ID"])["ACTUAL_QUANTITY"].sum())
        # rej_vendor=dict(sorted(rej.items(), key=lambda item: item[1],reverse=True))
        # key=list(rej_vendor.keys())
        # value=list(rej_vendor.values())
        # key=[str(i) for i in key]
        # fig = plt.figure(figsize = (10, 5))
        # plt.bar(key[0:5],value[0:5])
        # plt.xlabel("Vendor ")
        # plt.ylabel("Quantity ")
        # plt.title("Top 5 Vendor with highest rejection")
        # for i ,v in enumerate(value[0:5]):
        #     plt.text(i,v,str(v),ha='center')
        # st.pyplot(fig)
        rej_qn=dict(rej_df.groupby([ 'VENDOR_ID' , 'ITEM_ID' ])['ACTUAL_QUANTITY'].sum())
        tol_qn={}
        for i,j in rej_qn.items():
            tol_qn[i]=df_main.loc[(df_main['VENDOR_ID']==i[0]) & (df_main['ITEM_ID']==i[1]) & (df_main['TRANSACTION_TYPE']=='RECEIVE')]['ACTUAL_QUANTITY'].sum()
        rej_rate=[]
        for index, row in rej_df.iterrows():
            tol=tol_qn[(row['VENDOR_ID'],row['ITEM_ID'])]
            rej_rate.append((row['ACTUAL_QUANTITY']/tol)*100)
        # del(rej_df['REJECTION_RATE'])
        rej_df.insert(5,'REJECTION_RATE',rej_rate)
        # supp1=list(rej_df['VENDOR_ID'].unique())
        # inp1=st.selectbox(label="Vendor:", options=supp1)
        # diction={}
        # for i in supp1:
        #     diction[i]=list(rej_df.loc[rej_df['VENDOR_ID']==i]['ITEM_ID'].unique())
        # #inp2=st.selectbox(label="Item", options=diction[inp1])

        # inp2 = st.multiselect("Item",diction[inp1],diction[inp1][0])
        # # st.write(inp2)
        # # st.write(rej_df.loc[(rej_df['VENDOR_ID']==inp1)&(rej_df['ITEM_ID'].isin(inp2))])
        # search=st.checkbox("Advance Search") 
        # df1= rej_df.loc[(rej_df['VENDOR_ID']==inp1)&(rej_df['ITEM_ID'].isin(inp2))].sort_values(by=['ITEM_ID','TRANSACTION_DATE','REJECTION_RATE'])
        # start_1=list(df1.sort_values(by=['TRANSACTION_DATE']).head(1)['TRANSACTION_DATE'])
        # end_1=list(df1.sort_values(by=['TRANSACTION_DATE']).tail(1)['TRANSACTION_DATE']) 
        # if search:
        #     date_1=pd.to_datetime(st.date_input("Start date",start_1[0]))
        #     date_2=pd.to_datetime(st.date_input("End date",end_1[0]))
        #     df1= rej_df.loc[(rej_df['VENDOR_ID']==inp1) & (rej_df['ITEM_ID'].isin(inp2)) &(rej_df['TRANSACTION_DATE']>=date_1) &(rej_df['TRANSACTION_DATE']<=date_2) ].sort_values(by=['ITEM_ID','TRANSACTION_DATE','REJECTION_RATE'])
        
        # fig ,ax=plt.subplots()
        # fig = plt.figure(figsize=(12, 4))
        # rej_df.loc[rej_df['VENDOR_ID']==inp1].sort_values(by=['TRANSACTION_DATE']).groupby(['ITEM_ID'])['REJECTION_RATE'].plot(figsize=(12,6),legend=True)
        # fig = px.line(df1, x='TRANSACTION_DATE', y='REJECTION_RATE', color='ITEM_ID', symbol='ITEM_ID', markers=True).update_layout(
        #     xaxis_title="Date", yaxis_title="Rejection Rate")
        # st.plotly_chart(fig,use_container_width=True)

        def Trend(supp,slopes,time,inp):
            down_flag=0
            month=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            up_flag=0
            neutral_flag=0
            mon=[]
            for i in range(len(slopes)):
                for j in range(len(slopes[i])):
                    if slopes[i][j]<0.0:
                        up_flag=1
                    if slopes[i][j]>0.0:
                        down_flag=1
                    if slopes[i][j]==0:
                        neutral_flag=1
                    if slopes[i][j]<0:
                        mon.append(time[i])
            ne_flag=0
            if neutral_flag==1 and up_flag ==0 and down_flag==0:
                st.write("Vendor {0} has no irregularity detected".format(inp))
                ne_flag=1
            elif up_flag==0:
                st.write("Vendor {0} have a upward trend  ".format(inp))
            elif down_flag==0:
                st.write("Vendor {0} have an downward trend".format(inp))
            if ne_flag==0:    
                cycle_len=3
                flag=0
                count=0
                l=[]
                for i in range(len(slopes)):
                    for j in range(len(slopes[i])):
                        if slopes[i][j]>=0:
                            count+=1
                            if count>=cycle_len:
                                if flag!=1:
                                    l.append(time[j])
                                    l.append(time[j-1])
                                    flag=1       
                                else :
                                    l.append(time[j])
                                    flag=1
                        else:
                            flag=0
                            count=0
                if (len(l)!=0):
                    st.write("The deviation for {0} are in the months of:".format(inp))
                    l=list(set(l))
                    for i in l:
                        st.write(month[i-1])

        def Slope(df,inp):
            supp=list(df['VENDOR_ID'].unique())
            slopes=[]
            time=list(df['TRANSACTION_DATE'].dt.month)
            for i in supp:
                y=list(df.loc[df['VENDOR_ID']==i]['REJECTION_RATE'])
                slope=[0.0]
                N=len(y)
                x=[i for i in range(1,N+1)]
                for i in range(N):
                    if i+1<N:
                        slope.append((y[i+1]-y[i])/(x[i+1]-x[i]))
                slopes.append(slope)
            Trend(supp,slopes,time,inp)
        #     print(y)
            return slopes
        
        # Slope(df1,inp1)
        item_list=list(rej_df['ITEM_ID'].unique())
        inp3=st.selectbox(label="Item",options=item_list)
        diction={}
        for i in item_list:
            diction[i]=list(rej_df.loc[rej_df['ITEM_ID']==i]['VENDOR_ID'].unique())
        # lists=list(rej_df.loc[rej_df['ITEM_ID']==inp3]["VENDOR_ID"].unique())
        # inp4=st.selectbox(label="Vendor",options=lists)
        inp4 = st.multiselect("Vendor",diction[inp3],diction[inp3][0])
        temp_df= rej_df.loc[(rej_df['ITEM_ID']==inp3)&(rej_df['VENDOR_ID'].isin(inp4))].sort_values(by=['VENDOR_ID','TRANSACTION_DATE','REJECTION_RATE'])
        # temp_df=rej_df.loc[(rej_df['ITEM_ID']==inp3 )& (rej_df['VENDOR_ID']==inp4)].sort_values(by=['TRANSACTION_DATE','REJECTION_RATE'])
        # search_2=st.checkbox("Advance search")
        start_2=list(temp_df.head(1)['TRANSACTION_DATE'])
        end_2=list(temp_df.tail(1)['TRANSACTION_DATE'])   
        # if search_2:
        #     date_3=pd.to_datetime(st.date_input("Start Date",start_2[0]))
        #     date_4=pd.to_datetime(st.date_input("End Date",end_2[0]))
        #     temp_df= rej_df.loc[((rej_df['VENDOR_ID']==inp4) & (rej_df['ITEM_ID']==inp3))&(rej_df['TRANSACTION_DATE']>=date_3) &(rej_df['TRANSACTION_DATE']<=date_4) ].sort_values(by=['TRANSACTION_DATE','REJECTION_RATE'])
            
        fig = px.line(temp_df, x='TRANSACTION_DATE', y='REJECTION_RATE', color='VENDOR_ID', symbol='VENDOR_ID', markers=True).update_layout(
            xaxis_title="Date", yaxis_title="Rejection Rate")
        st.plotly_chart(fig,use_container_width=True)
        Slope(temp_df,inp4)
        # df2=rej_df.loc[(rej_df['ITEM_ID']==21635887)].sort_values(by=['TRANSACTION_DATE'])
        # fig = px.line(df2, x='TRANSACTION_DATE', y='REJECTION_RATE', color='VENDOR_ID', symbol='VENDOR_ID', markers=True).update_layout(
        #     xaxis_title="Date", yaxis_title="Rejection Rate")
        # st.plotly_chart(fig,use_container_width=True)
        # start=pd.to_datetime(str(st.date_input("Enter start date", datetime.date(2023, 6, 1))))
        # end = pd.to_datetime(str(st.date_input("Enter end date", datetime.date(2023, 8, 1))))
        # st.write("The dates are :",end-start)
        # df=rej_df.loc[(rej_df['ITEM_ID']==21635887) & (rej_df['TRANSACTION_DATE']>=start) & (rej_df['TRANSACTION_DATE']<=end)].sort_values(by=['TRANSACTION_DATE'])
        # st.write(df.head())
        # fig = px.line(df, x='TRANSACTION_DATE', y='REJECTION_RATE', color='VENDOR_ID', symbol='VENDOR_ID', markers=True).update_layout(
        # xaxis_title="Date", yaxis_title="Rejection Rate")
        # st.plotly_chart(fig,use_container_width=True)
    else:
        st.warning('Upload a File.') 
        
