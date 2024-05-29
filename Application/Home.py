import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import seaborn as sns
import plotly.express as px
from streamlit_option_menu import option_menu

st.set_page_config(page_title = 'Application')
st.title("Project")

with st.sidebar:
    selected=option_menu(
        menu_title='Main Menu',
        options=["Home"]
    )
if selected=='Home':
    file= st.file_uploader(label = 'Upload your dataset:')

    if file:
        st.write(file)
        po_receiving_data=pd.read_excel(file,na_values='Missing',usecols="C,F,M,O:P")
        st.success('File upload successfully.')
        df_main=po_receiving_data.copy()                          
        df_main['ITEM_ID'].fillna(-1,inplace=True)
        lists=[[4821176,21635887,200,'ACCEPT','2023-04-07'],[4821048,21635887,300,'ACCEPT','2023-08-28']]                           
        for i in lists:                                                                                                             
            df_main.loc[len(df_main.index)]=i                                                                                                                                                                                                         
        df_main['ITEM_ID']=pd.to_numeric(df_main['ITEM_ID'], downcast='integer', errors='coerce')               
        acpt_df=df_main.loc[(df_main['TRANSACTION_TYPE']=='ACCEPT') & (df_main['ITEM_ID']!=-1)].copy()
        a=pd.to_datetime(acpt_df['TRANSACTION_DATE'])                                                                               
        acpt_df['TRANSACTION_DATE']=pd.to_datetime(a.dt.strftime("%m-%d-%y")).copy()                                                
        acpt_df.reset_index(drop=True,inplace=True)  
        acpt_df['MONTH']=acpt_df['TRANSACTION_DATE']
        acpt_df.set_index('MONTH',inplace=True)
        st.header("Accepted data")
        st.write(acpt_df.tail())       
        rej_df=df_main.loc[ (df_main['ITEM_ID']!=-1) & ((df_main['TRANSACTION_TYPE']=='REJECT') | (df_main['TRANSACTION_TYPE']=='RETURN TO VENDOR') | (df_main['TRANSACTION_TYPE']=='RETURN TO RECEIVING') | (df_main['TRANSACTION_TYPE']=='TRANSFER')) ].copy()
        rej_df.reset_index(drop=True, inplace=True)
        st.header("Rejection data")
        st.write(rej_df.head())
        rej_df['REJECTION_RATE']=0.0
        add_list=[[4821048,21635887,20,'REJECT','2023-06-04',0.0],[4821048,21635887,40,'REJECT','2023-07-09',0.0],[4821048,21635887,60,'REJECT','2023-08-14',0.0],[4821176,21635887,10,'REJECT','2023-06-04',0.0],[4821176,21635887,20,'REJECT','2023-07-09',0.0],[4821176,21635887,30,'REJECT','2023-08-14',0.0],[4821186,21635887,10,'REJECT','2023-06-04',4.5],[4821186,21635887,20,'REJECT','2023-07-01',7.5],[4821186,21635887,30,'REJECT','2023-08-01',6.6]]
        for i in add_list:                                                                                                               
            rej_df.loc[len(rej_df.index)]=i                                             
        rej_df.reset_index(drop=True, inplace=True)                                                                                 
        rej_df['TRANSACTION_TYPE']='REJECT'                                              
        a=pd.to_datetime(rej_df['TRANSACTION_DATE'])                                                                                
        rej_df['TRANSACTION_DATE']=pd.to_datetime(a.dt.strftime("%m-%d-%y")).copy()                                         
        rej_df.reset_index(drop=True,inplace=True)       
        rej_df['MONTH']=rej_df['TRANSACTION_DATE']                                                                                  
        rej_df.set_index('MONTH',inplace=True)   
        st.header("Analysis")  
        fig,ax=plt.subplots(figsize=(18,6))                                                                                         
        sns.countplot(df_main['TRANSACTION_TYPE'])
        st.pyplot(fig)
        key=['ACCEPTED','REJECTED']
        values=[]
        values.append(acpt_df['ACTUAL_QUANTITY'].sum())
        values.append(rej_df['ACTUAL_QUANTITY'].sum())    
        fig1, ax1 = plt.subplots(figsize=(10,5))
        ax1.pie(values,labels=key,autopct="%1.1f%%")
        ax1.axis('equal')  
        plt.legend()
        st.pyplot(fig1)    
        rej=dict(rej_df.groupby(["VENDOR_ID"])["ACTUAL_QUANTITY"].sum())
        rej_vendor=dict(sorted(rej.items(), key=lambda item: item[1],reverse=True))
        key=list(rej_vendor.keys())
        value=list(rej_vendor.values())
        key=[str(i) for i in key]
        fig = plt.figure(figsize = (10, 5))
        plt.bar(key[0:5],value[0:5])
        plt.xlabel("Vendor ")
        plt.ylabel("Quantity ")
        plt.title("Top 5 Vendor with highest rejection")
        for i ,v in enumerate(value[0:5]):
            plt.text(i,v,str(v),ha='center')
        st.pyplot(fig)
        list1=dict(rej_df.groupby([ 'VENDOR_ID' , 'ITEM_ID' ])['ACTUAL_QUANTITY' ].sum())
        acpt={}
        for i,j in list1.items():
            acpt[i]=df_main.loc[(df_main['VENDOR_ID']==i[0]) & (df_main['ITEM_ID']==i[1])]['ACTUAL_QUANTITY'].sum()
        l=[]
        for index, row in rej_df.iterrows():
            tol=acpt[(row['VENDOR_ID'],row['ITEM_ID'])]
            l.append((row['ACTUAL_QUANTITY']/tol)*100)
        del(rej_df['REJECTION_RATE'])
        rej_df.insert(5,'REJECTION_RATE',l)
        supp1=list(rej_df['VENDOR_ID'].unique())
        inp1=st.selectbox(label="Supplier:", options=supp1)
        fig ,ax=plt.subplots()
        fig = plt.figure(figsize=(12, 4))
        # sns.scatterplot(data=df, x=df.index, y='REJECTION_RATE', color='red',hue='ITEM_ID')
        # sns.lineplot(data=df, x=df.index, y='REJECTION_RATE', color=' blue',hue='ITEM_ID')
        df1= rej_df.loc[rej_df['VENDOR_ID']==inp1].sort_values(by=['TRANSACTION_DATE'])
        rej_df.loc[rej_df['VENDOR_ID']==inp1].sort_values(by=['TRANSACTION_DATE']).groupby(['ITEM_ID'])['REJECTION_RATE'].plot(figsize=(12,6),legend=True)
        fig = px.line(df1, x='TRANSACTION_DATE', y='REJECTION_RATE', color='ITEM_ID', symbol='ITEM_ID', markers=True).update_layout(
            xaxis_title="Date", yaxis_title="Rejection Rate")
        st.plotly_chart(fig,use_container_width=True)
        # plt.xlabel('Month')
        # plt.ylabel('Rejected Rate')
        # plt.title('Rejected Rate over time')
        # plt.ylim(0,40)
        # plt.legend(title='VENDOR  ID',bbox_to_anchor=(1.05,1))
        # st.pyplot(fig)
        st.write('All items are stable for vendor', inp1)
        df2=rej_df.loc[(rej_df['ITEM_ID']==21635887)].sort_values(by=['TRANSACTION_DATE'])
        fig = px.line(df2, x='TRANSACTION_DATE', y='REJECTION_RATE', color='VENDOR_ID', symbol='VENDOR_ID', markers=True).update_layout(
            xaxis_title="Date", yaxis_title="Rejection Rate")
        st.plotly_chart(fig,use_container_width=True)
        def Trend(supp,slopes):
            down_flag=0
            up_flag=0
            for i in range(len(slopes)):
                for j in range(len(slopes[i])):
                    if slopes[i][j]<0.0:
                        up_flag=1
                    if slopes[i][j]>=0.0:
                        down_flag=1
            if up_flag==0:
                st.write("All Vendor have a upward trend")
            if down_flag==0:
                st.write("All Vendor have an downward trend")
        def Slope(df):
            supp=list(df['VENDOR_ID'].unique())
            slopes=[]
            for i in supp:
                y=list(df.loc[df['VENDOR_ID']==i]['REJECTION_RATE'])
                slope=[0.0]
                N=len(y)
                x=[i for i in range(1,N+1)]
                for i in range(N):
                    if i+1<N:
                        slope.append((y[i+1]-y[i])/(x[i+1]-x[i]))
                slopes.append(slope)
            Trend(supp,slopes)
            return slopes
        start=pd.to_datetime(str(st.date_input("Enter start date", value=None)))
        end = pd.to_datetime(str(st.date_input("Enter end date", value=None)))
        st.write("The dates are :",start,end)
        df=rej_df.loc[(rej_df['ITEM_ID']==21635887) & (rej_df['TRANSACTION_DATE']>=start) & (rej_df['TRANSACTION_DATE']<=end)].sort_values(by=['TRANSACTION_DATE'])
        st.write(df.head())
        fig = px.line(df, x='TRANSACTION_DATE', y='REJECTION_RATE', color='VENDOR_ID', symbol='VENDOR_ID', markers=True).update_layout(
        xaxis_title="Date", yaxis_title="Rejection Rate")
        st.plotly_chart(fig,use_container_width=True)
        Slope(df)
    else:
        st.warning('Upload a File.')

